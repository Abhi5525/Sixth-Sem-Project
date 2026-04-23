"""
Management command to fix inconsistent professional registration data.

This command identifies and fixes the following inconsistencies:
1. Users with is_professional=True but no ManpowerProfile (orphaned flags)
2. Users with is_professional=False but have APPROVED ManpowerProfile (missing flags)
3. Users with REJECTED ManpowerProfile but is_professional=True (should be False)
4. ManpowerProfiles with verification_status not matching is_professional flag
"""

from django.core.management.base import BaseCommand, CommandError
from users.models import CustomUser, ManpowerProfile
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix inconsistent professional registration data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about each fix',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('Starting professional registration data cleanup...'))
        self.stdout.write(f'Mode: {"DRY RUN" if dry_run else "LIVE"}')
        self.stdout.write('')
        
        fixes_applied = 0
        
        # Issue 1: Users with is_professional=True but no ManpowerProfile
        self.stdout.write(self.style.WARNING('Issue 1: Checking for orphaned is_professional flags...'))
        orphaned_users = CustomUser.objects.filter(
            is_professional=True
        ).exclude(
            manpowerprofile__isnull=False
        )
        
        if orphaned_users.exists():
            self.stdout.write(f'  Found {orphaned_users.count()} users with orphaned is_professional=True flag')
            for user in orphaned_users:
                if verbose:
                    self.stdout.write(f'    - User: {user.full_name} ({user.phone_number})')
                
                if not dry_run:
                    user.is_professional = False
                    user.save(update_fields=['is_professional'])
                    fixes_applied += 1
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ No orphaned flags found'))
        
        self.stdout.write('')
        
        # Issue 2: Users with APPROVED profile but is_professional=False
        self.stdout.write(self.style.WARNING('Issue 2: Checking for missing is_professional flags on approved professionals...'))
        missing_flag_users = CustomUser.objects.filter(
            is_professional=False,
            manpowerprofile__verification_status='APPROVED'
        )
        
        if missing_flag_users.exists():
            self.stdout.write(f'  Found {missing_flag_users.count()} approved professionals with is_professional=False')
            for user in missing_flag_users:
                if verbose:
                    self.stdout.write(f'    - User: {user.full_name} ({user.phone_number})')
                
                if not dry_run:
                    user.is_professional = True
                    user.save(update_fields=['is_professional'])
                    fixes_applied += 1
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ All approved professionals have correct flags'))
        
        self.stdout.write('')
        
        # Issue 3: Users with REJECTED profile but is_professional=True
        self.stdout.write(self.style.WARNING('Issue 3: Checking for rejected professionals with is_professional=True...'))
        rejected_with_flag = CustomUser.objects.filter(
            is_professional=True,
            manpowerprofile__verification_status='REJECTED'
        )
        
        if rejected_with_flag.exists():
            self.stdout.write(f'  Found {rejected_with_flag.count()} rejected professionals with is_professional=True')
            for user in rejected_with_flag:
                if verbose:
                    self.stdout.write(f'    - User: {user.full_name} ({user.phone_number})')
                
                if not dry_run:
                    user.is_professional = False
                    user.save(update_fields=['is_professional'])
                    fixes_applied += 1
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ All rejected professionals have correct flags'))
        
        self.stdout.write('')
        
        # Issue 4: PENDING professionals - should keep current flag state
        self.stdout.write(self.style.INFO('Issue 4: Checking PENDING professionals...'))
        pending_professionals = ManpowerProfile.objects.filter(
            verification_status='PENDING'
        ).select_related('user')
        
        if pending_professionals.exists():
            self.stdout.write(f'  Found {pending_professionals.count()} professionals with PENDING status')
            if verbose:
                for profile in pending_professionals:
                    self.stdout.write(f'    - User: {profile.user.full_name} ({profile.user.phone_number}), is_professional={profile.user.is_professional}')
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ No PENDING professionals found'))
        
        self.stdout.write('')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'DRY RUN COMPLETE: {fixes_applied} fixes would be applied'))
        else:
            self.stdout.write(self.style.SUCCESS(f'LIVE RUN COMPLETE: {fixes_applied} fixes applied'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
