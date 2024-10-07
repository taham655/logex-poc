import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from langchain_core.tools import tool
import os
from typing import Dict
import random
from datetime import datetime, timedelta

ORDER_DATABASE = {
    "ORD123456": {
        "status": "Processing",
        "details": "Order received and is being prepared for shipment",
        "estimated_delivery": (datetime.now() + timedelta(days=5)).isoformat()
    },
    "ORD789012": {
        "status": "In Transit",
        "details": "Package has left our facility and is en route to the destination",
        "estimated_delivery": (datetime.now() + timedelta(days=2)).isoformat()
    },
    "ORD345678": {
        "status": "Delivered",
        "details": "Package was delivered to the recipient",
        "delivery_date": (datetime.now() - timedelta(days=1)).isoformat()
    }
}

@tool
def track_order(order_id: str) -> Dict:
    """
    Track the status and details of an order.
    Args:
        order_id: Unique order identifier
    Returns:
        Dict with order_id, status, details, and either estimated_delivery or delivery_date
    """
    if order_id in ORDER_DATABASE:
        order_info = ORDER_DATABASE[order_id]
        result = {
            "order_id": order_id,
            "status": order_info["status"],
            "details": order_info["details"]
        }
        if order_info["status"] == "Delivered":
            result["delivery_date"] = order_info["delivery_date"]
        else:
            result["estimated_delivery"] = order_info["estimated_delivery"]
        return result
    else:
        return {"error": "Order not found", "order_id": order_id}


@tool
def estimate_delivery_time(order_id: str, destination_zip: str) -> Dict:
    """
    Estimate delivery time for an order.
    Args:
        order_id: Unique order identifier
        destination_zip: Delivery destination zip code
    Returns:
        Dict with order_id, destination_zip, and estimated_delivery (ISO format)
    """
    current_date = datetime.now()
    estimated_days = random.randint(1, 7)
    estimated_delivery = current_date + timedelta(days=estimated_days)
    return {
        "order_id": order_id,
        "destination_zip": destination_zip,
        "estimated_delivery": estimated_delivery.isoformat()
    }

@tool
def calculate_shipping_cost(length: float, width: float, height: float, weight: float) -> Dict:
    """
    Calculate shipping cost based on package dimensions and weight.
    Args:
        length: Package length in inches
        width: Package width in inches
        height: Package height in inches
        weight: Package weight in kilos
    Returns:
        Dict with package_dimensions, package_weight, and shipping_cost
    """
    volume = length * width * height
    shipping_cost = 5.00 + (volume * 0.01) + (weight * 0.5)
    return {
        "package_dimensions": f"{length}x{width}x{height} inches",
        "package_weight": f"{weight} lbs",
        "shipping_cost": round(shipping_cost, 2)
    }

@tool
def validate_address(street: str, city: str, state: str, zip_code: str) -> Dict:
    """
    Validate a given address.
    Args:
        street: Street address
        city: City name
        state: State abbreviation
        zip_code: ZIP code
    Returns:
        Dict with is_valid flag and address details (original or corrected)
    """
    is_valid = random.choice([True, False])
    if is_valid:
        return {"is_valid": True, "address": {"street": street, "city": city, "state": state, "zip_code": zip_code}}
    else:
        corrected_zip = zip_code[:-1] + str(int(zip_code[-1]) + 1)
        return {"is_valid": False, "suggested_correction": {"street": street, "city": city, "state": state, "zip_code": corrected_zip}}
    
    
