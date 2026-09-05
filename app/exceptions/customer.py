class CustomerError(Exception):
    pass


class CustomerHasOrdersError(CustomerError):
    pass
