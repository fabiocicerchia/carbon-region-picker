@domain:distribution @area:one-line-installer @from:carbon-region-picker/install
Feature: Installing with the one-line installer
  Lets a user install carbon-region-picker with a single piped shell command, without cloning the repository or knowing which Python installer they have.

  @id:distribution.one-line-installer.001 @rule:distribution.installer.prefers-pipx-falls-back-to-pip @inferred @source:install.sh#install.sh
  Scenario Outline: The installer uses pipx when available and a per-user pip install otherwise
    Given the user's machine <pipx_state>
    When the user runs the one-line installer
    Then the tool is installed from the latest source on the project's main branch with <installer>
    And the installer prints "carbon-region-picker installed. Run: carbon-region-picker --help"

    Examples:
      | pipx_state              | installer          |
      | has pipx on its PATH    | pipx install       |
      | has no pipx on its PATH | pip install --user |

  @id:distribution.one-line-installer.002 @rule:distribution.installer.no-success-claim-on-failure @inferred @source:install.sh#install.sh
  Scenario: A failed installation stops without claiming success
    Given the user's machine has no pipx, and pip is missing or the install from source fails
    When the user runs the one-line installer
    Then the installer exits with a non-zero status
    And the message "carbon-region-picker installed" is not printed
