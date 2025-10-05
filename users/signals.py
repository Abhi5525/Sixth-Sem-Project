from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import  ManpowerProfile
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
