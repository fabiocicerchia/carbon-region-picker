@domain:command-line @area:options-validation @from:carbon-region-picker/carbon-region-picker
Feature: Refusing live-only options without live data
  Serves operators by stopping flag combinations that would silently do nothing.

  @id:command-line.options-validation.001 @rule:command-line.options-validation.live-only-flags-require-live @verified @source:carbon_region_picker.py#main @test:tests/test_carbon_region_picker.py#test_marginal_without_live_rejected @test:tests/test_carbon_region_picker.py#test_forecast_without_live_rejected
  Scenario Outline: Marginal intensity and the forecast are refused without live data
    Given live data is not requested
    When the operator runs the tool with <flag>
    Then stderr shows "carbon-region-picker: --marginal/--forecast require --live"
    And the tool exits with status 64
    And no ranking is printed

    Examples:
      | flag       |
      | --marginal |
      | --forecast |
