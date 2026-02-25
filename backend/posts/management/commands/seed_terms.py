from django.core.management.base import BaseCommand
from posts.models import Term

BASE_TERMS = [
    # Dishes / cuisines
    "ramen", "pho", "shawarma", "birria", "tacos", "burrito",
    "sushi", "dumplings", "pad thai", "bibimbap",
    "pizza", "pasta", "lasagna",

    # Ingredients
    "garlic", "ginger", "miso", "gochujang", "kimchi",
    "tahini", "chickpeas", "lentils", "tofu",
    "cottage cheese", "greek yogurt",

    # Drinks / desserts
    "matcha", "boba", "tiramisu",

    # Cooking tools / styles
    "air fryer", "slow cooker", "meal prep",
]

# optional “do-not-track” junk words (you can expand)
DEFAULT_STOP_TERMS = [
    "food", "cook", "cooking", "recipe", "recipes",
    "help", "need", "best", "easy", "good", "question",
    "cutting", "dinner", "lunch", "breakfast",
]

class Command(BaseCommand):
    help = "Seed Term table with a curated list of food-related terms."

    def add_arguments(self, parser):
        parser.add_argument("--deactivate-stops", action="store_true",
                            help="Ensure stop terms exist but are set is_active=False.")
        parser.add_argument("--wipe", action="store_true",
                            help="Delete all existing terms before seeding (use carefully).")

    def handle(self, *args, **opts):
        if opts["wipe"]:
            Term.objects.all().delete()
            self.stdout.write(self.style.WARNING("Wiped all existing terms."))

        created = 0
        reactivated = 0

        for t in BASE_TERMS:
            t = t.strip().lower()
            obj, was_created = Term.objects.get_or_create(text=t, defaults={"is_active": True})
            if was_created:
                created += 1
            else:
                if obj.is_active is False:
                    obj.is_active = True
                    obj.save(update_fields=["is_active"])
                    reactivated += 1

        stop_deactivated = 0
        if opts["deactivate_stops"]:
            for t in DEFAULT_STOP_TERMS:
                t = t.strip().lower()
                obj, _ = Term.objects.get_or_create(text=t, defaults={"is_active": False})
                if obj.is_active:
                    obj.is_active = False
                    obj.save(update_fields=["is_active"])
                    stop_deactivated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seeded terms. Created={created}, Reactivated={reactivated}, StopDeactivated={stop_deactivated}"
        ))