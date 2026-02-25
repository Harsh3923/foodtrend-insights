# posts/management/commands/import_terms.py

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from posts.models import Term


class Command(BaseCommand):
    help = "Import food terms from a text file (one term per line)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            required=True,
            help="Path to a .txt file with one term per line (lines starting with # are ignored).",
        )
        parser.add_argument(
            "--deactivate",
            action="store_true",
            help="Import terms as inactive (is_active=False). Default is active.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would happen without writing to the DB.",
        )

    def handle(self, *args, **opts):
        file_path = Path(opts["file"])
        if not file_path.exists() or not file_path.is_file():
            raise CommandError(f"File not found: {file_path}")

        make_active = not opts["deactivate"]
        dry_run = opts["dry_run"]

        created = 0
        reactivated = 0
        unchanged = 0
        skipped_blank = 0
        skipped_comment = 0

        lines = file_path.read_text(encoding="utf-8").splitlines()

        for raw in lines:
            line = (raw or "").strip()

            if not line:
                skipped_blank += 1
                continue

            if line.startswith("#"):
                skipped_comment += 1
                continue

            # normalize term text
            text = line.lower()

            existing = Term.objects.filter(text=text).first()

            if existing is None:
                if dry_run:
                    created += 1
                    continue

                Term.objects.create(text=text, is_active=make_active)
                created += 1
            else:
                # If term exists but is inactive and we’re importing as active -> reactivate
                if make_active and not existing.is_active:
                    if dry_run:
                        reactivated += 1
                        continue
                    existing.is_active = True
                    existing.save(update_fields=["is_active"])
                    reactivated += 1
                else:
                    unchanged += 1

        mode = "DRY RUN" if dry_run else "DONE"
        self.stdout.write(self.style.SUCCESS(
            f"{mode}: created={created}, reactivated={reactivated}, unchanged={unchanged}, "
            f"skipped_blank={skipped_blank}, skipped_comment={skipped_comment}"
        ))