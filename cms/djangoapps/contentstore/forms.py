from django import forms
from django.forms import ModelForm
from shoppingcart.models import Coupons

class CouponsForm(ModelForm):
    percentage_discount = forms.IntegerField(label="Percentage Discount", min_value=0)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}), label='Description')

    class Meta:
        model = Coupons
        exclude = ('created_by_id', 'created_at')