from django.db import migrations
from django.conf import settings
import os


def fix_site_domain(apps, schema_editor):
    """Fix the Site domain to match the production domain"""
    Site = apps.get_model('sites', 'Site')
    
    site_domain = os.environ.get('SITE_DOMAIN', 'farmerpricealert.onrender.com')
    
    try:
        site = Site.objects.get(id=settings.SITE_ID)
        if site.domain != site_domain:
            old_domain = site.domain
            site.domain = site_domain
            site.name = 'Farmer Price Alert'
            site.save()
            print(f"✅ Updated Site domain from '{old_domain}' to '{site_domain}'")
        else:
            print(f"✅ Site domain already correct: {site_domain}")
    except Site.DoesNotExist:
        Site.objects.create(
            id=settings.SITE_ID,
            domain=site_domain,
            name='Farmer Price Alert'
        )
        print(f"✅ Created Site with domain: {site_domain}")


def reverse_fix(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('farmerpricealert', '0008_setup_google_oauth'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(fix_site_domain, reverse_fix),
    ]
