#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, render_template, jsonify
from datetime import datetime
import json
import os

# 导入自定义模块
from modules.parser import TransactionParser
from modules.database import DatabaseManager
from modules.validator import TransactionValidator

app = Flask(__name__)

# 初始化模块
parser = TransactionParser()
db = DatabaseManager()
validator = TransactionValidator()


@app.route("/")
def index():
    """主页"""
    return render_template("index.html")


@app.route("/api/transaction", methods=["POST"])
def add_transaction():
    """添加交易记录"""
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify(
                {"success": False, "message": "请提供交易文本", "data": None}
            ), 400

        text = data["text"].strip()
        if not text:
            return jsonify(
                {"success": False, "message": "交易文本不能为空", "data": None}
            ), 400

        # 1. 解析文本
        parse_result = parser.parse(text)

        if not parse_result["success"]:
            # 解析失败，可能缺少信息
            return jsonify(
                {
                    "success": False,
                    "message": f"解析失败: {parse_result['message']}",
                    "data": {
                        "parse_result": parse_result,
                        "missing_info": parse_result.get("missing_info", []),
                    },
                }
            ), 200

        transaction_data = parse_result["data"]

        # 2. 验证数据
        validation_result = validator.validate_transaction(transaction_data)

        if not validation_result["is_valid"]:
            return jsonify(
                {
                    "success": False,
                    "message": f"数据验证失败: {'; '.join(validation_result['errors'])}",
                    "data": {
                        "transaction_data": transaction_data,
                        "validation_result": validation_result,
                    },
                }
            ), 200

        # 3. 保存到数据库
        transaction_id = db.save_transaction(transaction_data)

        # 4. 返回成功结果
        result = {
            "success": True,
            "message": "交易记录保存成功",
            "data": {
                "transaction_id": transaction_id,
                "transaction_data": transaction_data,
                "validation_result": validation_result,
            },
        }

        return jsonify(result)

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"系统错误: {str(e)}", "data": None}
        ), 500


@app.route("/api/balance/<account_name>")
def get_account_balance(account_name):
    """获取账户余额"""
    try:
        balance = db.get_account_balance(account_name)

        if balance is None:
            return jsonify(
                {
                    "success": False,
                    "message": f"账户 {account_name} 不存在",
                    "data": None,
                }
            ), 404

        return jsonify(
            {
                "success": True,
                "message": "查询成功",
                "data": {"account_name": account_name, "balance": balance},
            }
        )

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"查询失败: {str(e)}", "data": None}
        ), 500


@app.route("/api/balances")
def get_all_balances():
    """获取所有账户余额"""
    try:
        balances = db.get_all_balances()

        return jsonify(
            {
                "success": True,
                "message": "查询成功",
                "data": {"balances": balances, "total_accounts": len(balances)},
            }
        )

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"查询失败: {str(e)}", "data": None}
        ), 500


@app.route("/api/transactions/search")
def search_transactions():
    """搜索交易记录"""
    try:
        # 获取查询参数
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        account_name = request.args.get("account")
        category = request.args.get("category")
        keyword = request.args.get("keyword")
        limit = int(request.args.get("limit", 50))

        # 搜索交易
        transactions = db.search_transactions(
            start_date=start_date,
            end_date=end_date,
            account_name=account_name,
            category=category,
            keyword=keyword,
            limit=limit,
        )

        return jsonify(
            {
                "success": True,
                "message": f"找到 {len(transactions)} 条记录",
                "data": {"transactions": transactions, "count": len(transactions)},
            }
        )

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"搜索失败: {str(e)}", "data": None}
        ), 500


@app.route("/api/report/monthly")
def get_monthly_report():
    """获取月度报表"""
    try:
        year = int(request.args.get("year", datetime.now().year))
        month = int(request.args.get("month", datetime.now().month))

        report = db.get_monthly_summary(year, month)

        return jsonify({"success": True, "message": "报表生成成功", "data": report})

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"报表生成失败: {str(e)}", "data": None}
        ), 500


@app.route("/api/transaction/<int:transaction_id>", methods=["DELETE"])
def delete_transaction(transaction_id):
    """删除交易记录"""
    try:
        success = db.delete_transaction(transaction_id)

        if success:
            return jsonify(
                {
                    "success": True,
                    "message": f"交易 {transaction_id} 删除成功",
                    "data": None,
                }
            )
        else:
            return jsonify(
                {
                    "success": False,
                    "message": f"交易 {transaction_id} 不存在",
                    "data": None,
                }
            ), 404

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"删除失败: {str(e)}", "data": None}
        ), 500


@app.route("/api/validate")
def validate_accounts():
    """验证账户余额一致性"""
    try:
        validation_result = db.validate_accounts_balance()

        return jsonify(
            {"success": True, "message": "验证完成", "data": validation_result}
        )

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"验证失败: {str(e)}", "data": None}
        ), 500


@app.route("/api/config")
def get_config():
    """获取配置信息（用于前端显示选项）"""
    try:
        # 获取可用的账户和分类
        categories = parser.categories
        accounts = parser.accounts

        return jsonify(
            {
                "success": True,
                "message": "配置获取成功",
                "data": {
                    "expense_categories": list(
                        categories.get("expense_categories", {}).keys()
                    ),
                    "income_categories": list(
                        categories.get("income_categories", {}).keys()
                    ),
                    "asset_accounts": list(accounts.get("asset_accounts", {}).keys()),
                    "liability_accounts": list(
                        accounts.get("liability_accounts", {}).keys()
                    ),
                },
            }
        )

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"配置获取失败: {str(e)}", "data": None}
        ), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "接口不存在", "data": None}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "服务器内部错误", "data": None}), 500


if __name__ == "__main__":
    host = os.environ.get("MOECHAT_FINANCIAL_HOST", "127.0.0.1")
    port = int(os.environ.get("MOECHAT_FINANCIAL_PORT", "5000"))

    print("=== 财务记录系统启动 ===")
    print(f"访问地址: http://{host}:{port}")
    print("API文档:")
    print("  POST /api/transaction - 添加交易")
    print("  GET  /api/balance/<账户名> - 查询余额")
    print("  GET  /api/balances - 查询所有余额")
    print("  GET  /api/transactions/search - 搜索交易")
    print("  GET  /api/report/monthly - 月度报表")
    print("  DELETE /api/transaction/<ID> - 删除交易")
    print("  GET  /api/validate - 验证账户余额")
    print("  GET  /api/config - 获取配置")
    print("========================")

    # 启动Flask应用
    app.run(host=host, port=port, debug=True)
