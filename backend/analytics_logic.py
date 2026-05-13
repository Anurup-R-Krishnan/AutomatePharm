from datetime import datetime, timedelta
from sqlalchemy import func, desc
from .extensions import db
from .models.sales import SalesBill, SalesBillItem
from .models.core import Item, Customer
import math

def calculate_linear_regression(data):
    """
    Simple linear regression: y = mx + c
    data: list of (x, y) tuples where x is the day index and y is the sales value
    Returns: m, c
    """
    n = len(data)
    if n < 2:
        return 0, 0
    
    sum_x = sum(x for x, y in data)
    sum_y = sum(y for x, y in data)
    sum_xx = sum(x * x for x, y in data)
    sum_xy = sum(x * y for x, y in data)
    
    numerator_m = (n * sum_xy) - (sum_x * sum_y)
    denominator_m = (n * sum_xx) - (sum_x * sum_x)
    
    if denominator_m == 0:
        return 0, 0
        
    m = numerator_m / denominator_m
    c = (sum_y - (m * sum_x)) / n
    
    return m, c

def get_sales_forecast(days_back=30, forecast_days=7):
    """
    Forecast sales for the next few days based on history.
    """
    start_date = datetime.utcnow().date() - timedelta(days=days_back)
    
    # Get daily sales totals
    daily_sales = db.session.query(
        SalesBill.bill_date,
        func.sum(SalesBill.net_amount).label('total')
    ).filter(
        SalesBill.bill_date >= start_date,
        SalesBill.is_cancelled == False
    ).group_by(SalesBill.bill_date).order_by(SalesBill.bill_date).all()
    
    if not daily_sales:
        return {
            "forecast": [], 
            "trend": "stable", 
            "growth_rate": 0, 
            "historical": []
        }
        
    # Prepare data for regression
    min_date = daily_sales[0][0]
    data = []
    for d, total in daily_sales:
        x = (d - min_date).days
        data.append((x, float(total)))
        
    m, c = calculate_linear_regression(data)
    
    forecast = []
    last_day_index = data[-1][0] if data else 0
    
    for i in range(1, forecast_days + 1):
        x_future = last_day_index + i
        y_future = max(0, m * x_future + c)
        date_future = min_date + timedelta(days=x_future)
        forecast.append({
            "date": date_future.isoformat(),
            "predicted_sales": round(y_future, 2)
        })
        
    trend = "up" if m > 0.1 else "down" if m < -0.1 else "stable"
    
    return {
        "forecast": forecast,
        "trend": trend,
        "growth_rate": round(m, 4),
        "historical": [{"date": d.isoformat(), "total": float(t)} for d, t in daily_sales]
    }

def get_top_moving_items(limit=10, days_back=30):
    """
    Find items with the highest sales volume (Frequently Moving).
    """
    start_date = datetime.utcnow().date() - timedelta(days=days_back)
    
    top_items = db.session.query(
        SalesBillItem.item_id,
        Item.item_name,
        func.sum(SalesBillItem.qty_sold).label('total_qty')
    ).join(SalesBill, SalesBillItem.bill_id == SalesBill.bill_id).join(Item, SalesBillItem.item_id == Item.item_id).filter(
        SalesBill.bill_date >= start_date,
        SalesBill.is_cancelled == False
    ).group_by(SalesBillItem.item_id, Item.item_name).order_by(desc('total_qty')).limit(limit).all()
    
    return [
        {"item_id": item_id, "name": item_name, "quantity": int(total_qty)}
        for item_id, item_name, total_qty in top_items
    ]

def get_market_basket_analysis(limit=5):
    """
    Identify items frequently bought together (Affinity).
    """
    recent_bill_ids = db.session.query(SalesBill.bill_id).order_by(desc(SalesBill.created_at)).limit(500).subquery()
    
    from sqlalchemy.orm import aliased
    i1 = aliased(SalesBillItem)
    i2 = aliased(SalesBillItem)
    
    pairs = db.session.query(
        i1.item_id,
        i2.item_id,
        func.count('*').label('frequency')
    ).join(i2, i1.bill_id == i2.bill_id).filter(
        i1.item_id < i2.item_id,
        i1.bill_id.in_(recent_bill_ids)
    ).group_by(i1.item_id, i2.item_id).order_by(desc('frequency')).limit(limit).all()
    
    result = []
    for id1, id2, freq in pairs:
        item1 = db.session.query(Item.item_name).filter_by(item_id=id1).first()
        item2 = db.session.query(Item.item_name).filter_by(item_id=id2).first()
        result.append({
            "item1": item1[0] if item1 else id1,
            "item2": item2[0] if item2 else id2,
            "frequency": int(freq)
        })
        
    return result

def get_churn_risk_customers(days_threshold=60, min_total_spend=500):
    """
    Find customers who used to buy a lot but haven't visited in a while.
    """
    threshold_date = datetime.utcnow().date() - timedelta(days=days_threshold)
    
    customer_stats = db.session.query(
        SalesBill.customer_id,
        func.max(SalesBill.bill_date).label('last_visit'),
        func.sum(SalesBill.net_amount).label('total_spend')
    ).filter(
        SalesBill.customer_id != None,
        SalesBill.is_cancelled == False
    ).group_by(SalesBill.customer_id).subquery()
    
    churn_risk = db.session.query(
        Customer.customer_name,
        Customer.phone,
        customer_stats.c.last_visit,
        customer_stats.c.total_spend
    ).join(customer_stats, Customer.customer_id == customer_stats.c.customer_id).filter(
        customer_stats.c.last_visit < threshold_date,
        customer_stats.c.total_spend >= min_total_spend
    ).order_by(desc(customer_stats.c.total_spend)).limit(10).all()
    
    return [
        {
            "name": name,
            "phone": phone,
            "last_visit": last_visit.isoformat(),
            "total_spend": float(total_spend),
            "days_since_last_visit": (datetime.utcnow().date() - last_visit).days
        }
        for name, phone, last_visit, total_spend in churn_risk
    ]
