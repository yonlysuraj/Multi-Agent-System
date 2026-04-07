"""
Mini e-commerce checkout app — intentionally buggy.
Bug: payment_service.process_payment() doesn't handle None gateway response.
"""


class PaymentGateway:
    """Simulates an external payment gateway."""

    def charge(self, payment_request: dict) -> object | None:
        """
        Simulate payment processing.
        Returns None for high-value orders (simulating gateway timeout
        during extended fraud check).
        """
        amount = payment_request.get("amount", 0)

        if amount > 500:
            # Simulate: gateway times out during fraud check for high-value orders
            # Returns None instead of a response object
            return None

        # Normal successful response
        return PaymentResponse(
            transaction_id=f"TXN-{hash(str(payment_request)) % 100000:05d}",
            status="success",
            amount=amount
        )


class PaymentResponse:
    """Gateway response object."""

    def __init__(self, transaction_id: str, status: str, amount: float):
        self.transaction_id = transaction_id
        self.status = status
        self.amount = amount


class PaymentService:
    """Handles payment processing — contains the bug."""

    def __init__(self):
        self.gateway = PaymentGateway()

    def process_payment(self, order: dict) -> dict:
        """
        Process a payment for an order.

        BUG: Line below assumes gateway always returns a response object.
        When gateway returns None (timeout on high-value orders),
        accessing .transaction_id raises AttributeError.
        """
        payment_request = {
            "amount": order["total"],
            "currency": "USD",
            "user_id": order["user_id"],
            "order_id": order["order_id"]
        }

        # Call gateway
        gateway_response = self.gateway.charge(payment_request)

        # BUG IS HERE: No None check!
        # When gateway returns None for orders > $500, this crashes
        txn_id = gateway_response.transaction_id  # <- AttributeError if None

        return {
            "success": True,
            "transaction_id": txn_id,
            "amount": order["total"]
        }


def handle_checkout(user_id: int, items: list, total: float):
    """Simulate the checkout endpoint."""
    order = {
        "user_id": user_id,
        "order_id": f"ORD-{user_id}-{int(total)}",
        "items": items,
        "total": total
    }

    service = PaymentService()
    try:
        result = service.process_payment(order)
        print(f"Payment successful: {result}")
        return result
    except Exception as e:
        print(f"Payment failed: {e}")
        raise


if __name__ == "__main__":
    # Test 1: Small order — should work
    print("--- Test 1: Small order ($45.99) ---")
    handle_checkout(user_id=4521, items=["shirt"], total=45.99)

    print()

    # Test 2: Large order — should crash (the bug)
    print("--- Test 2: Large order ($549.99) ---")
    handle_checkout(user_id=1188, items=["laptop"], total=549.99)
