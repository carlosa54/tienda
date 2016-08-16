from django import forms
from .models import Variation
from django.forms import modelformset_factory
from django.contrib.auth.forms import UserCreationForm

class VariationInventoryForm(forms.ModelForm):
	class Meta:
		model = Variation
		fields = [
			"price",
			"sale_price",
			"inventory",
			"active"
			]

VariationInventoryFormSet = modelformset_factory(Variation, form=VariationInventoryForm, extra=0)