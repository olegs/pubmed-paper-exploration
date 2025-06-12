import pytest
from src.parsing.age.get_age import get_age
from src.model.geo_sample import GEOSample


@pytest.mark.parametrize(
    "sample,expected_age",
    [
        (GEOSample({"characteristics_ch1": [
            "age: 20"]}), 20),
        (GEOSample({"characteristics_ch1": [
            "age (years): 20"]}), 20),
        (GEOSample({"characteristics_ch1": [
            "age yrs: 20"]}), 20),
        (GEOSample({"characteristics_ch1": [
         "age (weeks): 20"]}), 20 * (7 / 365)),
        (GEOSample({"characteristics_ch1": [
            "age (ds): 12"]}), 12 / 365),
        (GEOSample({"characteristics_ch1": [
            "age_days: 10"]}), 10 / 365),
        (GEOSample({"characteristics_ch1": [
            "donor_age: 30"]}), 30),
        (GEOSample({"characteristics_ch1": [
            "donor_age: 18 months"]}), 1.5),
        (GEOSample({"characteristics_ch1": [
            "donor_age: 18 years"]}), 18),
        (GEOSample({"characteristics_ch1": [
            "donor_age: 18 days"]}), 18 / 365),
        (GEOSample({"characteristics_ch1": [
         "donor_age: 10-20 days"]}), (10 / 365, 20 / 365)),
        (GEOSample({"characteristics_ch1": [
         "age (months): 25 months"]}), 25 / 12),
        (GEOSample({"characteristics_ch1": [
         "donor_age_weeks: 13"]}), 13 * (7 / 365)),
        (GEOSample({"characteristics_ch1": [
         "donor_age_days: 13-25 d"]}), (13 / 365, 25 / 365)),
    ]
)
def test_get_age(sample: GEOSample, expected_age: float):
    assert get_age(sample) == pytest.approx(expected_age, 0.1)
