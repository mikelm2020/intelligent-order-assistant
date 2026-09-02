class OrderError(Exception):
    pass


class CustomerNotFoundError(OrderError):
    pass


class ProductNotFoundError(OrderError):
    pass


class InactiveProductError(OrderError):
    pass


class InsufficientStockError(OrderError):
    pass
