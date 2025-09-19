import click
import json
from pathlib import Path
from flask import current_app
from flask.cli import with_appcontext
from moments.core.extensions import db
from moments.models import Role
from moments.models import Photo
from moments.ml.gemini import generate_alt_text, generate_objects


def register_commands(app):
    @app.cli.command('init-db')
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def init_db_command(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command('init-app')
    def init_app_command():
        """Initialize Moments."""
        db.create_all()
        click.echo('Initialized the database.')

        Role.init_role()
        click.echo('Initialized the roles and permissions.')

    @app.cli.command('lorem')
    @click.option('--user', default=10, help='Quantity of users, default is 10.')
    @click.option('--follow', default=30, help='Quantity of follows, default is 30.')
    @click.option('--photo', default=30, help='Quantity of photos, default is 30.')
    @click.option('--tag', default=20, help='Quantity of tags, default is 20.')
    @click.option('--collect', default=50, help='Quantity of collects, default is 50.')
    @click.option('--comment', default=100, help='Quantity of comments, default is 100.')
    def lorem_command(user, follow, photo, tag, collect, comment):
        """Generate fake data."""
        from moments.lorem import fake_admin, fake_collect, fake_comment, fake_follow, fake_photo, fake_tag, fake_user

        db.drop_all()
        db.create_all()

        Role.init_role()
        click.echo('Initialized the roles and permissions.')
        fake_admin()
        click.echo('Generated the administrator.')
        fake_user(user)
        click.echo(f'Generated {user} users.')
        fake_follow(follow)
        click.echo(f'Generated {follow} follows.')
        fake_tag(tag)
        click.echo(f'Generated {tag} tags.')
        fake_photo(photo)
        click.echo(f'Generated {photo} photos.')
        fake_collect(collect)
        click.echo(f'Generated {collect} collects.')
        fake_comment(comment)
        click.echo(f'Generated {comment} comments.')
        click.echo('Done.')

    # -------- NEW: Backfill ML fields for existing photos --------
    @app.cli.command('ml-backfill')
    @click.option('--force', is_flag=True, help='Regenerate even if fields already exist.')
    @click.option('--limit', type=int, default=0, help='Process only the first N photos.')
    def ml_backfill(force: bool, limit: int):
        """
        Generate auto_alt_text and auto_tags_json for existing photos.

        Only generates alt text when the user did NOT provide a description,
        unless --force is used.
        """
        upload_path: Path = current_app.config['MOMENTS_UPLOAD_PATH']
        q = Photo.query
        total = q.count()
        processed = updated = 0

        for p in q.yield_per(50):
            if limit and processed >= limit:
                break

            abs_path = upload_path / p.filename
            if not abs_path.exists():
                click.echo(f"Skip (file missing): {abs_path}")
                processed += 1
                continue

            changed = False

            # Auto ALT only when no manual description (or if --force)
            if (not p.description) and (force or not p.auto_alt_text):
                try:
                    p.auto_alt_text = generate_alt_text(abs_path)
                    changed = True
                except Exception as e:
                    click.echo(f"[ALT] photo {p.id} failed: {e}")

            # Objects list (JSON) when empty (or if --force)
            if force or not p.auto_tags_json:
                try:
                    objs = generate_objects(abs_path)
                    p.auto_tags_json = json.dumps(objs)
                    changed = True
                except Exception as e:
                    click.echo(f"[TAGS] photo {p.id} failed: {e}")

            if changed:
                db.session.add(p)
                updated += 1

            processed += 1
            if processed % 50 == 0:
                db.session.commit()
                click.echo(f"Progress: {processed}/{total} processed, {updated} updated")

        db.session.commit()
        click.echo(f"Done. {processed} processed, {updated} updated.")
