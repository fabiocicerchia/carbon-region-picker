@domain:documentation-site @area:theme-palette @from:docs/stylesheets
Feature: Presenting the documentation in the project's own palette
  Gives docs readers one consistent green GreenOps look across the rendered docs and the splash page, without the pages loading anything over the network.

  Background:
    Given the documentation site is built with the project's theme stylesheet

  @id:documentation-site.theme-palette.003 @rule:docs.theme.no-network-assets @inferred @source:docs/stylesheets/extra.css#:root
  Scenario: Documentation pages load no fonts or styles from the network
    Given the reader's device has no internet access
    When a reader opens the documentation
    Then text is shown in the device's system sans-serif font
    And code is shown in the device's system monospace font
    And no web font, CDN asset or analytics script is requested
