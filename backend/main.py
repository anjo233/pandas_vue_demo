# backend/main.py

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional # 1. 导入 Optional 类型

app = FastAPI()

# CORS 中间件配置保持不变
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 原始数据和月份顺序
ALL_SALES_DATA = {
    'month': ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'],
    'sales': [250, 310, 280, 400, 350, 420, 480, 450, 500, 550, 600, 620]
}
MONTH_ORDER = ALL_SALES_DATA['month']

def select_month_indices(start_month: Optional[str], end_month: Optional[str],
                          month_order_list: list[str]) -> tuple[int, int]:
    start_index = 0

    if start_month and start_month in month_order_list:
        start_index = month_order_list.index(start_month)
        
    end_index = len(month_order_list) - 1
    if end_month and end_month in month_order_list:
        end_index = month_order_list.index(end_month)

    if start_index > end_index:
        start_index, end_index = end_index, start_index

    return start_index, end_index


@app.get("/api/sales")
def get_sales(start_month: Optional[str] = None, end_month: Optional[str] = None):

    df = pd.DataFrame(ALL_SALES_DATA)
    start_index, end_index = select_month_indices(start_month, end_month, MONTH_ORDER)
    # 根据索引筛选出需要的月份范围
    selected_months = MONTH_ORDER[start_index : end_index + 1]
    # 使用 .isin() 方法筛选 DataFrame
    filtered_df = df[df['month'].isin(selected_months)]

    return filtered_df.to_dict(orient='records')


@app.get("/api/kpi")
def get_kpi_summary():
    df = pd.DataFrame(ALL_SALES_DATA)
    total_sales = int(df['sales'].sum()) # <--- 需要的数据
    
    return {
        "total_sales": total_sales,
    }

@app.get("/api/month_pct")
def get_month_pct(start_month: Optional[str] = None, end_month: Optional[str] = None):

    df = pd.DataFrame(ALL_SALES_DATA)
    user_start_index, user_end_index = select_month_indices(start_month, end_month, MONTH_ORDER)
    
    actual_start_index = user_start_index
    if actual_start_index > 0:
        actual_start_index -= 1
    
    extended_months = MONTH_ORDER[actual_start_index : user_end_index + 1]
    extended_df = df[df["month"].isin(extended_months)].copy()

    extended_df["growth_rate"] = (extended_df["sales"].pct_change().fillna(0) * 100).round(2)   
    
    final_df = extended_df.iloc[1:] if actual_start_index < user_start_index else extended_df

    return final_df[["month", "growth_rate"]].to_dict(orient="records")

@app.get("/")
def read_root():
    return {"message": "欢迎来到 FastAPI 数据后端！"}