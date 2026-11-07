@domain:live-grid-data @area:api-credentials @from:carbon-region-picker/carbon-region-picker
Feature: Supplying the Electricity Maps token
  Serves operators enabling live data, who must provide an API token without leaking it.

  @id:live-grid-data.api-credentials.001 @rule:live-grid-data.api-credentials.live-requires-token @verified @source:carbon_region_picker.py#main @test:tests/test_carbon_region_picker.py#test_missing_token_returns_error
  Scenario: Live mode is refused without a token
    Given no token is passed on the command line
    And the EM_TOKEN environment variable is not set
    When the operator asks for a live ranking
    Then stderr shows "carbon-region-picker: --live needs --em-token or EM_TOKEN"
    And the tool exits with status 64
    And no ranking is printed

  @id:live-grid-data.api-credentials.002 @rule:live-grid-data.api-credentials.flag-over-env @inferred @source:carbon_region_picker.py#resolve_token
  Scenario Outline: A token on the command line takes precedence over EM_TOKEN
    Given EM_TOKEN is set to <env>
    And the command line passes token <flag>
    When the operator asks for a live ranking
    Then Electricity Maps is queried with token <used>

    Examples:
      | env            | flag            | used            |
      | em_env_example | em_flag_example | em_flag_example |
      | em_env_example | (none)          | em_env_example  |
