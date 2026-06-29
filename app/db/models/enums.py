import enum


class StartupRole(enum.StrEnum):
    founder = "founder"
    engineering = "engineering"
    product = "product"
    growth = "growth"
    marketing = "marketing"
    customer_success = "customer_success"
    operations = "operations"
    people_hiring = "people_hiring"


STARTUP_ROLE_LABELS: dict[StartupRole, str] = {
    StartupRole.founder: "Founder",
    StartupRole.engineering: "Engineering",
    StartupRole.product: "Product",
    StartupRole.growth: "Growth",
    StartupRole.marketing: "Marketing",
    StartupRole.customer_success: "Customer Success",
    StartupRole.operations: "Operations",
    StartupRole.people_hiring: "People & Hiring",
}


def startup_role_label(role: StartupRole) -> str:
    return STARTUP_ROLE_LABELS[role]
