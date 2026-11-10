@domain:live-grid-data @area:cleanest-hour-forecast @from:carbon-region-picker/carbon-region-picker
Feature: Suggesting the cleanest hour to run
  Serves engineers scheduling batch work, by pointing at the lowest-carbon hour ahead for the top region.

  Background:
    Given the operator has a valid Electricity Maps token
    And asks for a live ranking with the cleanest-hour forecast

  @id:live-grid-data.cleanest-hour-forecast.001 @rule:live-grid-data.cleanest-hour-forecast.lowest-slot-for-top-region @verified @source:carbon_region_picker.py#best_forecast_slot @test:tests/test_carbon_region_picker.py#test_best_forecast_slot_picks_lowest @test:tests/test_carbon_region_picker.py#test_render_includes_forecast_note @test:tests/test_carbon_region_picker.py#test_fetch_forecast_returns_list
  Scenario: The lowest-intensity forecast hour of the top region is suggested
    Given eu-north-1 ranks first
    And its zone forecast is 120 at 2026-07-15T22:00:00Z, 40 at 2026-07-16T02:00:00Z and 90 at 2026-07-16T06:00:00Z
    When the operator ranks aws regions near eu
    Then the report ends with "Cleanest hour in the next 24h for `eu-north-1`: 2026-07-16T02:00:00Z (40 gCO2e/kWh)."

  @id:live-grid-data.cleanest-hour-forecast.002 @rule:live-grid-data.cleanest-hour-forecast.omitted-without-data @verified @source:carbon_region_picker.py#fetch_forecast @test:tests/test_carbon_region_picker.py#test_best_forecast_slot_empty
  Scenario Outline: No cleanest hour is suggested when there is no forecast or no region
    Given <situation>
    When the operator ranks aws regions near eu
    Then no "Cleanest hour" line is shown
    And the ranking is printed and the tool exits with status 0

    Examples:
      | situation                                                      |
      | Electricity Maps returns no forecast for the top region's zone |
      | Electricity Maps refuses the forecast request                  |
      | the latency cap leaves no region                               |
