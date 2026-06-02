"""Seed the reactive Product demo with groups, users, and grouped products.

Idempotent: re-running updates existing rows in place (matched by name /
username) rather than duplicating, so it doubles as a reset. The data is shaped
to make per-user visibility (GroupFacet, see LOGIN.md / MATCHING.md) observable:
products are spread across two groups plus a public bucket, and the users sit in
different groups so each sees a different slice.

    ./manage.py seed_demo

Then log in (password ``demo``) as alice (sales), bob (ops), carol (both) or
boss (staff) and watch /crud/products/ show a different set for each.
"""
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from ryzom_example_crud.models import Product

# username -> (group names, is_staff). Password is 'demo' for everyone.
USERS = {
    'alice': (['sales'], False),
    'bob': (['ops'], False),
    'carol': (['sales', 'ops'], False),
    'boss': ([], True),
}

# name -> (price, stock_qty, group name or None for public)
PRODUCTS = {
    'Public Widget': ('9.99', 20, None),
    'Public Bolt': ('1.50', 0, None),
    'Public Hinge': ('3.75', 7, None),
    'Sales Cog': ('4.25', 12, 'sales'),
    'Sales Gear': ('7.80', 3, 'sales'),
    'Sales Lever': ('2.00', 0, 'sales'),
    'Sales Pulley': ('5.40', 9, 'sales'),
    'Ops Gadget': ('15.00', 8, 'ops'),
    'Ops Sprocket': ('3.30', 5, 'ops'),
    'Ops Valve': ('11.10', 0, 'ops'),
    'Ops Flange': ('6.60', 14, 'ops'),
}


class Command(BaseCommand):
    help = 'Seed the reactive Product demo (groups, users, grouped products).'

    def handle(self, *args, **options):
        groups = {
            name: Group.objects.get_or_create(name=name)[0]
            for name in ('sales', 'ops')
        }

        for username, (group_names, is_staff) in USERS.items():
            user, _ = User.objects.get_or_create(username=username)
            user.is_staff = is_staff
            user.set_password('demo')          # reset each run, known password
            user.save()
            user.groups.set([groups[g] for g in group_names])

        for name, (price, stock, group_name) in PRODUCTS.items():
            Product.objects.update_or_create(
                name=name,
                defaults=dict(
                    price=price,
                    stock_qty=stock,
                    group=groups[group_name] if group_name else None,
                ),
            )

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(groups)} groups, {len(USERS)} users '
            f'(password "demo"), {len(PRODUCTS)} products.'
        ))
        self.stdout.write(
            'Log in as alice (sales) / bob (ops) / carol (both) / boss (staff) '
            'at /login/ and open /crud/products/.'
        )
