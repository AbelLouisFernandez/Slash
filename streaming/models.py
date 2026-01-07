from django.db import models

# Create your models here.
class StreamingService(models.Model):
    name = models.CharField(max_length=50)
    country = models.CharField(max_length=2, default="IN")
    monthly_price = models.DecimalField(max_digits=6, decimal_places=2)
    last_updated = models.DateField(auto_now=True)
    supported_devices = models.CharField(max_length=250,default="smartphone")
    per_month = models.BooleanField(default=True);

    def __str__(self):
        return f"{self.name} ({self.country})"
