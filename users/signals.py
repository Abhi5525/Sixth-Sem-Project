from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import  ManpowerProfile, CustomUser
from bookings.models import RatingReview

@receiver(post_save, sender=RatingReview)
def update_professional_rating(sender, instance, **kwargs):
    professional = instance.professional
    reviews = RatingReview.objects.filter(professional=professional)

    professional.total_reviews = reviews.count()
    professional.average_rating = (
        sum(r.rating for r in reviews) / professional.total_reviews if professional.total_reviews > 0 else 0
    )
    professional.save(update_fields=["average_rating", "total_reviews"])


@receiver(post_delete, sender=RatingReview)
def update_professional_rating_on_delete(sender, instance, **kwargs):
    professional = instance.professional
    reviews = RatingReview.objects.filter(professional=professional)

    professional.total_reviews = reviews.count()
    professional.average_rating = (
        sum(r.rating for r in reviews) / professional.total_reviews if professional.total_reviews > 0 else 0
    )
    professional.save(update_fields=["average_rating", "total_reviews"])


@receiver(post_save, sender=ManpowerProfile)
def sync_professional_flag_on_status_change(sender, instance, created, **kwargs):
    """
    Signal handler to keep is_professional flag in sync with verification_status.
    
    Rules:
    - When status becomes REJECTED: set is_professional=False
    - When status becomes APPROVED: ensure is_professional=True
    - When status is PENDING: keep current is_professional state (allow re-verification)
    """
    user = instance.user
    
    # Only sync if user exists and is a CustomUser
    if not user or not isinstance(user, CustomUser):
        return
    
    # Get the old instance from database to compare status changes
    if not created:
        try:
            old_instance = ManpowerProfile.objects.get(pk=instance.pk)
            old_status = old_instance.verification_status
        except ManpowerProfile.DoesNotExist:
            old_status = None
    else:
        old_status = None
    
    new_status = instance.verification_status
    
    # Case 1: Status changed to REJECTED
    if new_status == 'REJECTED' and old_status != 'REJECTED':
        if user.is_professional:
            user.is_professional = False
            user.save(update_fields=['is_professional'])
    
    # Case 2: Status changed to APPROVED
    elif new_status == 'APPROVED' and old_status != 'APPROVED':
        if not user.is_professional:
            user.is_professional = True
            user.save(update_fields=['is_professional'])


@receiver(post_delete, sender=ManpowerProfile)
def reset_professional_flag_on_profile_deletion(sender, instance, **kwargs):
    """
    Signal handler to reset is_professional flag when ManpowerProfile is deleted.
    
    This ensures that when a professional deletes their profile (or admin deletes it),
    the user returns to default client state (is_professional=False).
    """
    user = instance.user
    
    # Only reset if user exists and is a CustomUser
    if not user or not isinstance(user, CustomUser):
        return
    
    # Reset the professional flag
    if user.is_professional:
        user.is_professional = False
        user.save(update_fields=['is_professional'])
