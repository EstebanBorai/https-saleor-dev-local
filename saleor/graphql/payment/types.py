import graphene
from graphene import relay

from ...core.permissions import OrderPermissions
from ...core.tracing import traced_resolver
from ...payment import models
from ..core.connection import CountableDjangoObjectType
from ..core.types import Money
from ..decorators import permission_required
from .enums import OrderAction, PaymentChargeStatusEnum


class Transaction(CountableDjangoObjectType):
    amount = graphene.Field(Money, description="Total amount of the transaction.")

    class Meta:
        description = "An object representing a single payment."
        interfaces = [relay.Node]
        model = models.Transaction
        filter_fields = ["id"]
        only_fields = [
            "id",
            "created",
            "payment",
            "token",
            "kind",
            "is_success",
            "error",
            "gateway_response",
        ]

    @staticmethod
    def resolve_amount(root: models.Transaction, _info):
        return root.get_amount()


class CreditCard(graphene.ObjectType):
    brand = graphene.String(description="Card brand.", required=True)
    first_digits = graphene.String(
        description="First 4 digits of the card number.", required=False
    )
    last_digits = graphene.String(
        description="Last 4 digits of the card number.", required=True
    )
    exp_month = graphene.Int(
        description=("Two-digit number representing the card’s expiration month."),
        required=False,
    )
    exp_year = graphene.Int(
        description=("Four-digit number representing the card’s expiration year."),
        required=False,
    )


class PaymentSource(graphene.ObjectType):
    class Meta:
        description = (
            "Represents a payment source stored "
            "for user in payment gateway, such as credit card."
        )

    gateway = graphene.String(description="Payment gateway name.", required=True)
    payment_method_id = graphene.String(description="ID of stored payment method.")
    credit_card_info = graphene.Field(
        CreditCard, description="Stored credit card details if available."
    )


class Payment(CountableDjangoObjectType):
    charge_status = PaymentChargeStatusEnum(
        description="Internal payment status.", required=True
    )
    actions = graphene.List(
        OrderAction,
        description=(
            "List of actions that can be performed in the current state of a payment."
        ),
        required=True,
    )
    partial = graphene.Boolean(
        description=(
            "Indicates whether this payment will " "be processed as a partial payment."
        )
    )
    total = graphene.Field(Money, description="Total amount of the payment.")
    captured_amount = graphene.Field(
        Money, description="Total amount captured for this payment."
    )
    transactions = graphene.List(
        Transaction, description="List of all transactions within this payment."
    )
    available_capture_amount = graphene.Field(
        Money, description="Maximum amount of money that can be captured."
    )
    available_refund_amount = graphene.Field(
        Money, description="Maximum amount of money that can be refunded."
    )
    credit_card = graphene.Field(
        CreditCard, description="The details of the card used for this payment."
    )
    gateway_name = graphene.String(
        description="A human-readable name of the payment gateway plugin."
    )

    class Meta:
        description = "Represents a payment of a given type."
        interfaces = [relay.Node]
        model = models.Payment
        filter_fields = ["id"]
        only_fields = [
            "id",
            "gateway",
            "gateway_name",
            "is_active",
            "created",
            "modified",
            "token",
            "checkout",
            "order",
            "customer_ip_address",
            "payment_method_type",
            "psp_reference",
        ]

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_customer_ip_address(root: models.Payment, _info):
        return root.customer_ip_address

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_actions(root: models.Payment, _info):
        actions = []
        if root.can_capture():
            actions.append(OrderAction.CAPTURE)
        if root.can_refund():
            actions.append(OrderAction.REFUND)
        if root.can_void():
            actions.append(OrderAction.VOID)
        return actions

    @staticmethod
    @traced_resolver
    def resolve_total(root: models.Payment, _info):
        return root.get_total()

    @staticmethod
    def resolve_captured_amount(root: models.Payment, _info):
        return root.get_captured_amount()

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_transactions(root: models.Payment, _info):
        return root.transactions.all()

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_available_refund_amount(root: models.Payment, _info):
        if not root.can_refund():
            return None
        return root.get_captured_amount()

    @staticmethod
    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_available_capture_amount(root: models.Payment, _info):
        if not root.can_capture():
            return None
        return Money(amount=root.get_charge_amount(), currency=root.currency)

    @staticmethod
    def resolve_credit_card(root: models.Payment, _info):
        data = {
            "brand": root.cc_brand,
            "exp_month": root.cc_exp_month,
            "exp_year": root.cc_exp_year,
            "first_digits": root.cc_first_digits,
            "last_digits": root.cc_last_digits,
        }
        if not any(data.values()):
            return None
        return CreditCard(**data)

    @staticmethod
    def resolve_gateway_name(root: models.Payment, _info):
        return _info.context.plugins.get_plugin_name(root.gateway)


class PaymentInitialized(graphene.ObjectType):
    class Meta:
        description = (
            "Server-side data generated by a payment gateway. Optional step when the "
            "payment provider requires an additional action to initialize payment "
            "session."
        )

    gateway = graphene.String(description="ID of a payment gateway.", required=True)
    name = graphene.String(description="Payment gateway name.", required=True)
    data = graphene.JSONString(
        description="Initialized data by gateway.", required=False
    )
