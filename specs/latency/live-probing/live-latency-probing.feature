@domain:latency @area:live-probing @from:carbon-region-picker/carbon-region-picker
Feature: Probing real latency to regions
  Serves engineers who want the cap judged on their actual network, by timing a TCP connect to each region instead of trusting estimates.

  Background:
    Given Given the operator asks for measured latency

  @id:latency.live-probing.001 @rule:latency.live-probing.measured-replaces-estimate @verified @source:carbon_region_picker.py#rank @test:tests/test_carbon_region_picker.py#test_rank_uses_measured_latency_over_bundled @test:tests/test_carbon_region_picker.py#test_measure_latency_ms_success
  Scenario: A measured latency replaces the estimate and is what the cap is judged on
    Given region eu-north-1 answers a connect in 48.26 ms
    And a latency cap of 40 ms
    When the operator ranks aws regions near eu
    Then eu-north-1 is not listed
    And regions that answered within 40 ms are listed with their measured latency rounded to one decimal

  @id:latency.live-probing.002 @rule:latency.live-probing.unmeasured-keeps-estimate @verified @source:carbon_region_picker.py#measure_all @test:tests/test_carbon_region_picker.py#test_measure_latency_ms_unreachable @test:tests/test_carbon_region_picker.py#test_measure_all_unknown_provider_is_noop @questionable
  Scenario Outline: Regions that cannot be probed keep their bundled estimate
    Given <situation>
    When the operator ranks <provider> regions near eu
    Then <region> is listed with its bundled latency of <estimate>ms
    And no warning is printed

    Examples:
      | situation                                                  | provider | region     | estimate |
      | the endpoint of eu-west-3 does not answer within 2 seconds | aws      | eu-west-3  | 20.0     |
      | azure has no per-region endpoint                           | azure    | westeurope | 20.0     |
