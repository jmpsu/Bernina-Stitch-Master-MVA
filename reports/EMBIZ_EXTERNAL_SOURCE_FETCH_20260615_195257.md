# EMBIZ External Learning Source Fetch
Generated: 2026-06-15T19:52:58+02:00

## Mattermost collaboration platform
- URL: https://github.com/mattermost/mattermost.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/collaboration/mattermost
From https://github.com/mattermost/mattermost
   d418653..d90ea34  master     -> origin/master
Updating d418653..d90ea34
Fast-forward
 api/v4/source/system.yaml                          |    8 +-
 e2e-tests/cypress/package-lock.json                |  442 +-----
 e2e-tests/cypress/package.json                     |   10 +-
 e2e-tests/playwright/eslint.config.mjs             |    2 +-
 e2e-tests/playwright/lib/src/file.ts               |    3 +-
 e2e-tests/playwright/package-lock.json             |   30 +-
 e2e-tests/playwright/package.json                  |    2 +-
 server/channels/api4/access_control_test.go        |   69 +
 server/channels/api4/config.go                     |    5 +
 server/channels/api4/config_test.go                |   14 +
 server/channels/app/access_control.go              |   12 +
 server/channels/app/file.go                        |    5 +-
 server/channels/app/notification_push.go           |   49 +-
 server/channels/app/platform/service.go            |    6 +-
 server/channels/app/plugin_hooks_test.go           |  138 +-
 server/channels/app/post_metadata_test.go          |  204 ++-
 server/channels/app/users/profile_picture.go       |    3 +-
 server/channels/db/migrations/migrations.list      |    2 +
 server/channels/store/retrylayer/retrylayer.go     |    8 +-
 .../store/storetest/mocks/AttributesStore.go       |   48 +-
 server/channels/store/timerlayer/timerlayer.go     |   12 +-
 .../mocks/AccessControlServiceInterface.go         |   64 +-
 .../mocks/PolicyAdministrationPointInterface.go    |   64 +-
 server/enterprise/message_export/shared/shared.go  |    8 +-
 server/i18n/en.json                                |    4 +
 server/platform/shared/filestore/azurestore.go     |   57 +-
 .../platform/shared/filestore/azurestore_test.go   |   46 +-
 server/platform/shared/filestore/filesstore.go     |   56 +-
 .../platform/shared/filestore/filesstore_test.go   |   31 +-
 .../shared/filestore/mocks/s3CopyClient.go         |  122 ++
 server/platform/shared/filestore/s3store.go        |   54 +-
 .../shared/filestore/s3store_copyobject_test.go    |   79 +
 server/public/model/config.go                      |   25 +-
 server/public/model/config_test.go                 |  104 ++
 server/public/shared/httpservice/client_test.go    |   33 +
 server/public/shared/httpservice/httpservice.go    |   84 +-
 webapp/channels/.eslintignore                      |    3 -
 webapp/channels/eslint.config.mjs                  |    6 +-
 webapp/channels/package.json                       |    9 +-
 webapp/channels/src/actions/cloud.tsx              |    4 +-
 webapp/channels/src/actions/file_actions.ts        |    4 +-
 webapp/channels/src/actions/invite_actions.ts      |    8 +-
 webapp/channels/src/actions/marketplace.ts         |    2 +-
 webapp/channels/src/actions/websocket_actions.ts   |    8 +-
 .../modals/job_details/job_details_modal.tsx       |    2 +-
 .../searchable_sync_job_channel_list.test.tsx      |  128 ++
 .../searchable_sync_job_channel_list.tsx           |    9 +-
 .../admin_console/access_control/policies.tsx      |    2 +-
 .../policy_details/channel_list/channel_list.tsx   |    8 +-
 .../admin_console/audit_logging/index.tsx          |   91 +-
 .../brand_image_setting/brand_image_setting.tsx    |    2 +-
 .../classification_markings.test.tsx               |  269 +++-
 .../classification_markings.tsx                    |   72 +-
 .../components/classification_levels_table.tsx     |    2 +
 .../components/level_name_cell.tsx                 |    9 +-
 .../classification_markings/utils/presets.ts       |    6 +
 .../user_multiselector/user_multiselector.tsx      |    2 +-
 .../channel_list/channel_list.tsx                  |    7 +-
 .../group_settings/group_details/group_details.tsx |   10 +-
 .../group_settings/group_details/group_users.tsx   |    2 +-
 .../ip_filtering/ip_filtering_utils.ts             |    2 +-
 .../admin_console/list_table/pagination.tsx        |    8 +-
 .../manage_teams_modal/manage_teams_dropdown.tsx   |    2 +-
 .../guest_permissions_tree.tsx                     |    6 +-
 .../plugin_management/plugin_management.tsx        |    2 +-
 .../request_button/request_button.tsx              |    2 +-
 .../revoke_token_button/revoke_token_button.tsx    |    2 +-
 .../admin_console/save_changes_panel.tsx           |    6 +-
 .../admin_console/schema_admin_settings.tsx        |    2 +-
 .../modals/shared_channels_add_modal.tsx           |   17 +-
 .../secure_connection_detail.tsx                   |    5 +-
 .../components/admin_console/server_logs/logs.tsx  |    2 +-
 .../components/admin_console/system_users/index.ts |    2 +-
 .../channel/details/channel_details.tsx            |    2 +-
 .../channel/list/channel_list.tsx                  |    6 +-
 .../channels/src/components/admin_console/types.ts |    6 +-
 .../advanced_text_editor.test.tsx                  |   60 +
 .../advanced_text_editor/advanced_text_editor.tsx  |   11 +-
 .../composer_placeholder.test.ts                   |  179 +++
 .../advanced_text_editor/composer_placeholder.ts   |   55 +
 .../advanced_text_editor/formatting_bar/hooks.tsx  |   10 +-
 .../send_post_options/recent_used_custom_date.tsx  |    2 +-
 .../use_composer_placeholder.ts                    |   21 +
 .../advanced_text_editor/use_key_handler.tsx       |    6 +-
 .../use_post_box_indicator.tsx                     |    2 +-
 .../components/advanced_text_editor/use_submit.tsx |    2 +-
 .../apps_form_field/select_channel_option.test.tsx |   89 ++
 .../apps_form_field/select_channel_option.tsx      |    7 +-
 .../components/browse_channels/browse_channels.tsx |    2 +-
 .../channel_bookmarks_create_modal.tsx             |    2 +-
 .../channel_header/channel_header_title.test.tsx   |  113 ++
 .../channel_header/channel_header_title.tsx        |   10 +-
 .../channel_intro_renderer.test.tsx                |   70 +
 .../channel_intro_renderer.tsx                     |   25 +
 .../channel_invite_modal/channel_invite_modal.tsx  |   85 +-
 .../group_option/group_option.tsx                  |    2 +-
 .../channel_members_rhs/channel_members_rhs.tsx    |    4 +-
 .../channel_selector_modal.test.tsx                |   63 +
 .../channel_selector_modal.tsx                     |    9 +-
 .../channel_settings_access_rules_tab.tsx          |    2 +-
 .../channel_settings_configuration_tab.tsx         |   38 +-
 .../channel_type_icon/channel_icon.test.tsx        |  126 ++
 .../components/channel_type_icon/channel_icon.tsx  |   50 +
 .../channel_icon_override.test.ts                  |  337 ++++
 .../channel_type_icon/channel_icon_override.ts     |   66 +
 .../channel_type_icon/channel_type_icon.test.tsx   |  138 ++
 .../channel_type_icon/channel_type_icon.tsx        |   34 +
 .../compass_icon_resolver.test.ts                  |   50 +
 .../channel_type_icon/compass_icon_resolver.ts     |   19 +
 .../src/components/channel_type_icon/index.ts      |    7 +
 .../useChannelIconClassName.test.tsx               |   60 +
 .../channel_type_icon/useChannelIconClassName.ts   |   14 +
 .../useChannelIconOverrideName.test.tsx            |  102 ++
 .../useChannelIconOverrideName.ts                  |   30 +
 .../channel_view/channel_composer_banner.test.tsx  |   99 ++
 .../channel_view/channel_composer_banner.tsx       |   24 +
 .../src/components/channel_view/channel_view.tsx   |    2 +
 .../cloud_subscribe_result_modal/error.tsx         |    7 -
 webapp/channels/src/components/code_preview.tsx    |    2 +-
 .../hooks/useAccessControlAttributes.test.tsx      |    2 +-
 .../src/components/common/hooks/useCopyText.ts     |    2 +-
 .../create_recap_modal/channel_selector.test.tsx   |   75 +
 .../create_recap_modal/channel_selector.tsx        |   23 +-
 .../create_recap_modal/channel_summary.test.tsx    |   31 +
 .../create_recap_modal/channel_summary.tsx         |   43 +-
 .../create_recap_modal/create_recap_modal.tsx      |    2 +-
 .../custom_status/custom_status_emoji.tsx          |    2 +-
 .../custom_status/custom_status_modal.tsx          |    2 +-
 .../drafts/draft_title/draft_title.test.tsx        |   13 +
 .../components/drafts/draft_title/draft_title.tsx  |    7 +-
 .../components/edit_channel_header_modal/index.ts  |    2 +-
 .../forward_post_channel_select.test.tsx           |  285 ++++
 .../forward_post_channel_select.tsx                |   14 +-
 .../src/components/forward_post_modal/index.tsx    |    2 +-
 webapp/channels/src/components/get_link_modal.tsx  |    2 +-
 .../src/components/inline_entity_link/utils.ts     |    2 +-
 .../components/integrations/installed_command.tsx  |    4 +-
 .../invitation_modal/invitation_modal.tsx          |    4 +-
 .../keyboard_shortcuts.ts                          |    4 +-
 .../src/components/latex_block/latex_block.tsx     |   37 +-
 .../src/components/latex_inline/latex_inline.tsx   |   37 +-
 .../linking_landing_page/linking_landing_page.tsx  |    2 +-
 .../member_list_channel/member_list_channel.tsx    |    4 +-
 webapp/channels/src/components/menu/menu_item.tsx  |   14 +-
 .../src/components/mobile_sidebar_right/index.ts   |    2 +-
 .../src/components/multiselect/multiselect.tsx     |    2 +-
 .../components/multiselect/multiselect_list.tsx    |    2 +-
 .../src/components/payment_form/address_form.tsx   |    4 +-
 .../src/components/permalink_view/actions.ts       |    2 +-
 .../persist_notification_confirm_modal.tsx         |    2 +-
 .../marketplace_item_plugin.tsx                    |    6 +-
 webapp/channels/src/components/post/index.tsx      |    1 +
 .../src/components/post/post_component.test.tsx    |  105 ++
 .../src/components/post/post_component.tsx         |   51 +-
 .../channels/src/components/post_markdown/index.ts |    6 +-
 .../post_acknowledgements_users_popover.tsx        |    2 +-
 .../channel_intro_message.test.tsx                 |  184 +++
 .../channel_intro_message.tsx                      |   56 +-
 .../post_header_custom_status.tsx                  |    2 +-
 .../post_view/post_list_row/post_list_row.tsx      |    2 +-
 .../preparing_workspace/preparing_workspace.tsx    |    6 +-
 .../profile_popover_custom_status.tsx              |    2 +-
 .../profile_popover_other_user_row.tsx             |    2 +-
 .../channel_property_renderer.test.tsx             |   53 +-
 .../channel_property_renderer.tsx                  |    2 +-
 .../root_post_divider/root_post_divider.tsx        |    2 +-
 .../src/components/search_results/index.tsx        |   13 +-
 .../search_results/search_results.test.tsx         |    4 +-
 .../components/search_results/search_results.tsx   |   24 +-
 .../src/components/search_results/types.ts         |   48 -
 .../components/searchable_channel_list.test.tsx    |  114 +-
 .../src/components/searchable_channel_list.tsx     |    9 +-
 .../sidebar_category_menu/index.tsx                |    2 +-
 .../sidebar_base_channel.test.tsx                  |    2 +-
 .../sidebar_base_channel/sidebar_base_channel.tsx  |    2 +-
 .../sidebar_base_channel_icon.tsx                  |   23 +-
 .../sidebar_channel_icon.test.tsx                  |   58 +-
 .../sidebar_channel_icon/sidebar_channel_icon.tsx  |   15 +-
 .../sidebar_channel_link/sidebar_channel_link.tsx  |    3 +-
 webapp/channels/src/components/status_icon.tsx     |   24 +-
 .../suggestion/channel_mention_provider.test.tsx   |   98 +-
 .../suggestion/channel_mention_provider.tsx        |   61 +-
 .../suggestion/generic_channel_provider.test.tsx   |   53 +
 .../suggestion/generic_channel_provider.tsx        |    9 +-
 .../search_channel_suggestion.test.tsx.snap        |   10 +-
 .../search_channel_suggestion.test.tsx             |   52 +-
 .../search_channel_suggestion.tsx                  |   95 +-
 .../search_channel_with_permissions_provider.tsx   |   51 +-
 ...ch_channel_with_permissions_suggestion.test.tsx |  102 ++
 .../suggestion/switch_channel_provider.test.tsx    |   49 +
 .../suggestion/switch_channel_provider.tsx         |   12 +-
 .../terms_of_service/terms_of_service.tsx          |    2 +-
 .../thread_footer/thread_footer.tsx                |    2 +-
 .../global_threads/thread_list/thread_list.tsx     |    6 +-
 .../create_comment.test.tsx                        |  171 ++
 .../virtualized_thread_viewer/create_comment.tsx   |   20 +-
 .../create_and_join_channels_tour_tip.tsx          |    2 +-
 .../user_group_popover/user_group_popover.tsx      |    4 +-
 .../custom_theme_chooser/custom_theme_chooser.tsx  |    2 +-
 .../security/user_settings_security.tsx            |    2 +-
 .../view_user_group_modal.tsx                      |    6 +-
 .../widgets/inputs/users_emails_input.tsx          |    8 +-
 .../window_size_observer/WindowSizeObserver.tsx    |    6 +-
 .../channels/src/hooks/useChannelSystemPolicies.ts |    2 +-
 .../src/hooks/useGetCloudPreviewModalContent.ts    |    2 +-
 webapp/channels/src/i18n/en.json                   |    3 +-
 .../mattermost-redux/src/actions/errors.ts         |    2 +-
 .../mattermost-redux/src/actions/general.ts        |    2 +-
 .../packages/mattermost-redux/src/actions/roles.ts |    2 +-
 .../packages/mattermost-redux/src/actions/users.ts |    2 +-
 .../src/reducers/entities/schemes.ts               |    4 +-
 .../mattermost-redux/src/reducers/errors/index.ts  |    2 +-
 .../src/selectors/create_selector/index.d.ts       |    4 +-
 .../src/selectors/entities/report_a_problem.ts     |    2 +-
 .../src/selectors/entities/threads.ts              |    2 +-
 .../src/selectors/entities/users.ts                |   10 +-
 .../packages/mattermost-redux/src/store/index.ts   |    2 +
 .../packages/mattermost-redux/src/utils/helpers.ts |    3 +-
 webapp/channels/src/plugins/export.ts              |    2 +
 webapp/channels/src/plugins/registry.test.ts       |  267 ++++
 webapp/channels/src/plugins/registry.ts            |   99 ++
 webapp/channels/src/reducers/plugins/index.test.ts |   75 +
 webapp/channels/src/reducers/plugins/index.ts      |    4 +
 .../channels/src/selectors/channel_intro.test.ts   |  228 +++
 webapp/channels/src/selectors/channel_intro.ts     |   36 +
 .../channels/src/selectors/views/custom_status.ts  |    2 +-
 webapp/channels/src/stores/browser_store.tsx       |    4 +-
 webapp/channels/src/types/store/plugins.ts         |   23 +
 webapp/channels/src/utils/channel_utils.test.ts    |   26 +
 webapp/channels/src/utils/channel_utils.tsx        |   30 +-
 webapp/channels/src/utils/date_utils.ts            |    4 +-
 webapp/channels/src/utils/embed.tsx                |    2 +-
 .../src/utils/message_html_to_component.tsx        |    2 +-
 webapp/channels/src/utils/notifications.ts         |    2 +-
 webapp/channels/src/utils/plugin_error_log.test.ts |  141 ++
 webapp/channels/src/utils/plugin_error_log.ts      |   34 +
 webapp/channels/src/utils/post_utils.ts            |    6 +-
 webapp/channels/src/utils/properties.ts            |    6 +-
 webapp/channels/src/utils/syntax_highlighting.tsx  |    2 +-
 webapp/channels/src/utils/url.tsx                  |    2 +-
 webapp/channels/src/utils/utils.tsx                |   14 +-
 webapp/package-lock.json                           | 1667 ++++++++------------
 webapp/package.json                                |    7 +-
 .../patches/eslint-plugin-react-hooks+4.6.0.patch  |   26 -
 .../components/src/tour_tip/tour_tip_backdrop.tsx  |    2 +-
 webapp/platform/eslint-plugin/configs/base.js      |   13 +-
 webapp/platform/eslint-plugin/configs/react.js     |   44 +-
 webapp/platform/eslint-plugin/package.json         |   17 +-
 webapp/platform/shared/package.json                |    3 -
 webapp/platform/types/src/apps.ts                  |   15 +-
 webapp/platform/types/src/boards.ts                |    5 +-
 webapp/platform/types/src/bots.ts                  |   16 +-
 webapp/platform/types/src/emojis.ts                |   24 +-
 webapp/platform/types/src/plugins.ts               |    6 +-
 webapp/platform/types/src/utilities.ts             |    3 +-
 255 files changed, 7253 insertions(+), 2601 deletions(-)
 create mode 100644 server/platform/shared/filestore/mocks/s3CopyClient.go
 create mode 100644 server/platform/shared/filestore/s3store_copyobject_test.go
 delete mode 100644 webapp/channels/.eslintignore
 create mode 100644 webapp/channels/src/components/admin_console/access_control/modals/job_details/searchable_sync_job_channel_list.test.tsx
 create mode 100644 webapp/channels/src/components/advanced_text_editor/composer_placeholder.test.ts
 create mode 100644 webapp/channels/src/components/advanced_text_editor/composer_placeholder.ts
 create mode 100644 webapp/channels/src/components/advanced_text_editor/use_composer_placeholder.ts
 create mode 100644 webapp/channels/src/components/apps_form/apps_form_field/select_channel_option.test.tsx
 create mode 100644 webapp/channels/src/components/channel_intro_renderer/channel_intro_renderer.test.tsx
 create mode 100644 webapp/channels/src/components/channel_intro_renderer/channel_intro_renderer.tsx
 create mode 100644 webapp/channels/src/components/channel_type_icon/channel_icon.test.tsx
 create mode 100644 webapp/channels/src/components/channel_type_icon/channel_icon.tsx
 create mode 100644 webapp/channels/src/components/channel_type_icon/channel_icon_override.test.ts
 create mode 100644 webapp/channels/src/components/channel_type_icon/channel_icon_override.ts
 create mode 100644 webapp/channels/src/components/channel_type_icon/channel_type_icon.test.tsx
 create mode 100644 webapp/channels/src/components/channel_type_icon/channel_type_icon.tsx
 create mode 100644 webapp/channels/src/components/channel_type_icon/compass_icon_resolver.test.ts
 create mode 100644 webapp/channels/src/components/channel_type_icon/compass_icon_resolver.ts
 create mode 100644 webapp/channels/src/components/channel_type_icon/index.ts
 create mode 100644 webapp/channels/src/components/channel_type_icon/useChannelIconClassName.test.tsx
 create mode 100644 webapp/channels/src/components/channel_type_icon/useChannelIconClassName.ts
 create mode 100644 webapp/channels/src/components/channel_type_icon/useChannelIconOverrideName.test.tsx
 create mode 100644 webapp/channels/src/components/channel_type_icon/useChannelIconOverrideName.ts
 create mode 100644 webapp/channels/src/components/channel_view/channel_composer_banner.test.tsx
 create mode 100644 webapp/channels/src/components/channel_view/channel_composer_banner.tsx
 create mode 100644 webapp/channels/src/components/forward_post_modal/forward_post_channel_select.test.tsx
 delete mode 100644 webapp/channels/src/components/search_results/types.ts
 create mode 100644 webapp/channels/src/components/suggestion/generic_channel_provider.test.tsx
 create mode 100644 webapp/channels/src/components/suggestion/search_channel_with_permissions_suggestion.test.tsx
 create mode 100644 webapp/channels/src/components/threading/virtualized_thread_viewer/create_comment.test.tsx
 create mode 100644 webapp/channels/src/selectors/channel_intro.test.ts
 create mode 100644 webapp/channels/src/selectors/channel_intro.ts
 create mode 100644 webapp/channels/src/utils/plugin_error_log.test.ts
 create mode 100644 webapp/channels/src/utils/plugin_error_log.ts
 delete mode 100644 webapp/patches/eslint-plugin-react-hooks+4.6.0.patch
- Status: updated existing repo

## CRM AI Analysis / Text-to-SQL / medallion architecture
- URL: https://github.com/DiogoSoares3/CRM-AI-Analysis.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/analytics/crm-ai-analysis
Already up to date.
- Status: updated existing repo

## Addy Osmani agent skills
- URL: https://github.com/addyosmani/agent-skills.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/agent-skills/addyosmani-agent-skills
From https://github.com/addyosmani/agent-skills
   d187883..3a6fc63  main       -> origin/main
Updating d187883..3a6fc63
Fast-forward
 docs/antigravity-setup.md     |  3 ++-
 docs/gemini-cli-setup.md      |  3 ++-
 docs/getting-started.md       |  1 +
 hooks/hooks.json              |  2 +-
 hooks/simplify-ignore-test.sh |  0
 scripts/validate-skills.js    | 17 +++++++++++++++--
 6 files changed, 21 insertions(+), 5 deletions(-)
 mode change 100644 => 100755 hooks/simplify-ignore-test.sh
- Status: updated existing repo

## PM skills marketplace
- URL: https://github.com/phuryn/pm-skills.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/agent-skills/phuryn-pm-skills
Already up to date.
- Status: updated existing repo

## NVIDIA SkillSpector
- URL: https://github.com/NVIDIA/SkillSpector.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/security/nvidia-skillspector
From https://github.com/NVIDIA/SkillSpector
   1a7bf02..cff7ecc  main       -> origin/main
Updating 1a7bf02..cff7ecc
Fast-forward
 .dockerignore  | 22 +++++++++++++++++++++
 Dockerfile     | 16 ++++++++++++++++
 Makefile       |  7 ++++++-
 README.md      | 60 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++-
 pyproject.toml |  2 +-
 uv.lock        |  2 +-
 6 files changed, 105 insertions(+), 4 deletions(-)
 create mode 100644 .dockerignore
 create mode 100644 Dockerfile
- Status: updated existing repo

## Tolaria markdown knowledge base manager
- URL: https://github.com/refactoringhq/tolaria.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/knowledge-management/tolaria
From https://github.com/refactoringhq/tolaria
   b92d0c7..0e7726f  main                        -> origin/main
 * [new tag]         alpha-v2026.6.15-alpha.0008 -> alpha-v2026.6.15-alpha.0008
 * [new tag]         alpha-v2026.6.13-alpha.0002 -> alpha-v2026.6.13-alpha.0002
 * [new tag]         alpha-v2026.6.13-alpha.0003 -> alpha-v2026.6.13-alpha.0003
 * [new tag]         alpha-v2026.6.13-alpha.0004 -> alpha-v2026.6.13-alpha.0004
 * [new tag]         alpha-v2026.6.13-alpha.0005 -> alpha-v2026.6.13-alpha.0005
 * [new tag]         alpha-v2026.6.14-alpha.0001 -> alpha-v2026.6.14-alpha.0001
 * [new tag]         alpha-v2026.6.14-alpha.0002 -> alpha-v2026.6.14-alpha.0002
 * [new tag]         alpha-v2026.6.14-alpha.0003 -> alpha-v2026.6.14-alpha.0003
 * [new tag]         alpha-v2026.6.14-alpha.0004 -> alpha-v2026.6.14-alpha.0004
 * [new tag]         alpha-v2026.6.14-alpha.0005 -> alpha-v2026.6.14-alpha.0005
 * [new tag]         alpha-v2026.6.14-alpha.0006 -> alpha-v2026.6.14-alpha.0006
 * [new tag]         alpha-v2026.6.14-alpha.0007 -> alpha-v2026.6.14-alpha.0007
 * [new tag]         alpha-v2026.6.15-alpha.0001 -> alpha-v2026.6.15-alpha.0001
 * [new tag]         alpha-v2026.6.15-alpha.0002 -> alpha-v2026.6.15-alpha.0002
 * [new tag]         alpha-v2026.6.15-alpha.0003 -> alpha-v2026.6.15-alpha.0003
 * [new tag]         alpha-v2026.6.15-alpha.0004 -> alpha-v2026.6.15-alpha.0004
 * [new tag]         alpha-v2026.6.15-alpha.0005 -> alpha-v2026.6.15-alpha.0005
 * [new tag]         alpha-v2026.6.15-alpha.0006 -> alpha-v2026.6.15-alpha.0006
 * [new tag]         alpha-v2026.6.15-alpha.0007 -> alpha-v2026.6.15-alpha.0007
 * [new tag]         v2026-06-14                 -> v2026-06-14
Updating b92d0c7..0e7726f
Fast-forward
 .chunk/README.md                                   |  63 ++++
 .chunk/config.json                                 | 157 ++++++++
 .chunk/install-playwright-browsers.mjs             | 100 ++++++
 .chunk/run-playwright-shards.sh                    | 146 ++++++++
 .chunk/run-playwright-smoke.sh                     |  94 +++++
 .chunk/run-rust-gate.sh                            |  30 ++
 .chunk/run-sidecar-gates-local.sh                  | 395 +++++++++++++++++++++
 .chunk/run-sidecar-gates.sh                        | 115 ++++++
 .chunk/run-sidecar-lane.sh                         | 127 +++++++
 .husky/pre-commit                                  |  97 +----
 .husky/pre-push                                    | 159 +++++----
 AGENTS.md                                          |   8 +-
 docs/ABSTRACTIONS.md                               |   4 +-
 docs/ARCHITECTURE.md                               |  14 +-
 docs/GETTING-STARTED.md                            |  35 ++
 package.json                                       |   2 +-
 public/ai-agent-icons/SOURCES.md                   |   1 +
 public/ai-agent-icons/hermes.svg                   |   6 +
 release-notes/v2026-06-14.md                       |  14 +
 scripts/playwright-smoke-server.mjs                |   8 +-
 scripts/run-vitest-coverage-shards.mjs             | 200 +++++++++++
 scripts/run-vitest-coverage.mjs                    |  52 ++-
 src-tauri/src/ai_agents.rs                         | 134 +++----
 src-tauri/src/commands/ai.rs                       |   8 +
 src-tauri/src/hermes_cli.rs                        | 278 +++++++++++++++
 src-tauri/src/hermes_discovery.rs                  |  87 +++++
 src-tauri/src/lib.rs                               |   2 +
 src-tauri/src/settings.rs                          |  20 +-
 src-tauri/src/vault/cache.rs                       |  28 +-
 src-tauri/src/vault/getting_started.rs             |   6 +-
 src-tauri/src/window_state.rs                      |  26 +-
 src/App.test.tsx                                   |   9 +-
 src/components/AiAgentIcon.tsx                     |   1 +
 src/components/CommandPalette.test.tsx             |  49 ++-
 src/components/CommandPalette.tsx                  |  12 +-
 src/components/ConfirmDeleteDialog.test.tsx        |  24 +-
 src/components/Editor.test.tsx                     |  63 ++++
 src/components/Editor.tsx                          |   2 +
 src/components/NoteSearchList.test.tsx             |  16 +-
 src/components/NoteSearchList.tsx                  |  14 +-
 src/components/QuickOpenPalette.test.tsx           |  56 ++-
 src/components/Sidebar.typeActions.test.tsx        |  31 +-
 src/components/Sidebar.viewActions.test.tsx        |  95 +++++
 src/components/contextMenuPosition.ts              |  44 ++-
 .../editorSchema.markdownHighlight.test.ts         |  14 +
 .../markdownHighlightInputExtension.test.ts        |  18 +-
 src/components/markdownHighlightInputExtension.ts  |   7 +
 src/components/richEditorPaste.ts                  |  51 +++
 src/components/richEditorRecoveryClassifier.ts     |   3 +-
 ...chEditorTransformErrorRecoveryExtension.test.ts |  12 +
 src/components/sidebar/SidebarSections.tsx         |  30 +-
 src/components/sidebar/SidebarViewActions.tsx      |  15 +-
 src/components/status-bar/AiAgentsBadge.test.tsx   |   3 +
 src/components/titleHeadingInteractions.test.ts    | 107 ++++++
 src/components/titleHeadingInteractions.ts         |   9 +-
 src/components/titleHeadingPasteTarget.ts          |  34 ++
 src/components/ui/overlayPresence.test.tsx         |  12 +-
 src/components/ui/tooltip.tsx                      |  90 +----
 src/hooks/appCommandDispatcher.test.ts             |  11 +
 src/hooks/commands/aiAgentCommands.test.ts         |  27 ++
 src/hooks/editorFocusUtils.extra.test.ts           | 136 +++++--
 src/hooks/editorFocusUtils.ts                      |  81 +----
 src/hooks/editorTitleHeadingText.ts                |  24 ++
 src/hooks/editorTitleSelection.ts                  |  71 ++++
 src/hooks/useAiAgentPreferences.test.ts            |   2 +
 src/hooks/useAiAgentsStatus.test.ts                |   2 +
 src/hooks/useVaultLoader.test.ts                   |  20 +-
 src/lib/aiAgentStreamCallbacks.test.ts             |  50 +++
 src/lib/aiAgentStreamCallbacks.ts                  |  34 +-
 src/lib/aiAgents.test.ts                           |   6 +-
 src/lib/aiAgents.ts                                |   9 +-
 src/lib/aiTargets.test.ts                          |  10 +-
 src/lib/telemetry.test.ts                          |  27 ++
 src/lib/telemetry.ts                               |  51 ++-
 src/main.test.ts                                   |  14 +
 src/main.tsx                                       |   4 +-
 src/utils/markdownHighlightMarkdown.test.ts        |  14 +
 src/utils/markdownHighlightMarkdown.ts             |   8 +-
 src/utils/mouseMovement.test.ts                    |  65 ++++
 src/utils/mouseMovement.ts                         |  44 +++
 tests/smoke/fix-ai-chat-empty-body-v3.spec.ts      |   2 +-
 tests/smoke/h1-title-decoupled.spec.ts             |   6 +-
 tests/smoke/h1-untitled-auto-rename.spec.ts        |  10 +-
 tests/smoke/helpers.ts                             |  18 +-
 tests/smoke/keyboard-command-routing.spec.ts       |  14 +-
 .../literal-asterisk-paste-regression.spec.ts      |  63 ++++
 tests/smoke/missing-active-vault-recovery.spec.ts  |   2 +-
 tests/smoke/vault-loading-skeleton.spec.ts         |   2 +-
 vite.config.ts                                     |   1 +
 89 files changed, 3526 insertions(+), 539 deletions(-)
 create mode 100644 .chunk/README.md
 create mode 100644 .chunk/config.json
 create mode 100644 .chunk/install-playwright-browsers.mjs
 create mode 100644 .chunk/run-playwright-shards.sh
 create mode 100644 .chunk/run-playwright-smoke.sh
 create mode 100644 .chunk/run-rust-gate.sh
 create mode 100755 .chunk/run-sidecar-gates-local.sh
 create mode 100644 .chunk/run-sidecar-gates.sh
 create mode 100755 .chunk/run-sidecar-lane.sh
 create mode 100644 public/ai-agent-icons/hermes.svg
 create mode 100644 release-notes/v2026-06-14.md
 create mode 100644 scripts/run-vitest-coverage-shards.mjs
 create mode 100644 src-tauri/src/hermes_cli.rs
 create mode 100644 src-tauri/src/hermes_discovery.rs
 create mode 100644 src/components/Sidebar.viewActions.test.tsx
 create mode 100644 src/components/richEditorPaste.ts
 create mode 100644 src/components/titleHeadingInteractions.test.ts
 create mode 100644 src/components/titleHeadingPasteTarget.ts
 create mode 100644 src/hooks/editorTitleHeadingText.ts
 create mode 100644 src/hooks/editorTitleSelection.ts
 create mode 100644 src/utils/mouseMovement.test.ts
 create mode 100644 src/utils/mouseMovement.ts
 create mode 100644 tests/smoke/literal-asterisk-paste-regression.spec.ts
- Status: updated existing repo

## Obra superpowers agentic methodology
- URL: https://github.com/obra/superpowers.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/agent-skills/obra-superpowers
Already up to date.
- Status: updated existing repo

## Restic backup system
- URL: https://github.com/restic/restic.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/backup/restic
From https://github.com/restic/restic
   bf56d71..7d36449  master     -> origin/master
Updating bf56d71..7d36449
Fast-forward
 changelog/unreleased/issue-21866                   |   8 +
 changelog/unreleased/issue-3129                    |   7 +
 changelog/unreleased/pull-21876                    |   8 +
 changelog/unreleased/pull-21879                    |   7 +
 cmd/restic/cmd_backup.go                           |   5 +-
 cmd/restic/cmd_cache.go                            |   3 +-
 cmd/restic/cmd_cat.go                              |  11 +-
 cmd/restic/cmd_check.go                            |  10 +-
 cmd/restic/cmd_check_test.go                       |   4 +-
 cmd/restic/cmd_copy.go                             |  18 +-
 cmd/restic/cmd_copy_integration_test.go            |  12 +-
 cmd/restic/cmd_debug.go                            |   5 +-
 cmd/restic/cmd_diff.go                             |   5 +-
 cmd/restic/cmd_dump.go                             |   3 +-
 cmd/restic/cmd_find.go                             |  34 ++--
 cmd/restic/cmd_find_integration_test.go            |  23 ++-
 cmd/restic/cmd_forget.go                           |   5 +-
 cmd/restic/cmd_generate.go                         |   2 +-
 cmd/restic/cmd_init.go                             |   2 +-
 cmd/restic/cmd_init_integration_test.go            |   6 +-
 cmd/restic/cmd_key_add.go                          |   2 +-
 cmd/restic/cmd_key_integration_test.go             |  12 +-
 cmd/restic/cmd_key_list.go                         |   2 +-
 cmd/restic/cmd_key_passwd.go                       |   2 +-
 cmd/restic/cmd_key_remove.go                       |   2 +-
 cmd/restic/cmd_list.go                             |   3 +-
 cmd/restic/cmd_list_integration_test.go            |  10 +-
 cmd/restic/cmd_ls.go                               |   3 +-
 cmd/restic/cmd_migrate.go                          |   2 +-
 cmd/restic/cmd_mount.go                            |   5 +-
 cmd/restic/cmd_mount_integration_test.go           |   4 +-
 cmd/restic/cmd_prune.go                            |  33 ++-
 cmd/restic/cmd_prune_integration_test.go           |  25 +++
 cmd/restic/cmd_recover.go                          |   9 +-
 cmd/restic/cmd_repair_index.go                     |   3 +-
 cmd/restic/cmd_repair_packs.go                     |   3 +-
 cmd/restic/cmd_repair_snapshots.go                 |   5 +-
 cmd/restic/cmd_restore.go                          |   2 +-
 cmd/restic/cmd_rewrite.go                          |   2 +-
 cmd/restic/cmd_rewrite_integration_test.go         |   7 +-
 cmd/restic/cmd_self_update.go                      |   3 +-
 cmd/restic/cmd_snapshots.go                        |  10 +-
 cmd/restic/cmd_stats.go                            | 114 ++---------
 cmd/restic/cmd_stats_test.go                       |  28 ---
 cmd/restic/cmd_tag.go                              |   3 +-
 cmd/restic/cmd_unlock.go                           |   3 +-
 cmd/restic/cmd_version.go                          |   4 +-
 cmd/restic/integration_helpers_test.go             |  43 ++--
 cmd/restic/integration_test.go                     |   4 +-
 cmd/restic/lock.go                                 |   4 +-
 cmd/restic/main.go                                 |   5 +-
 doc/060_forget.rst                                 |   2 +
 doc/075_scripting.rst                              |  97 ++++++++-
 internal/archiver/archiver.go                      |  24 +--
 internal/archiver/archiver_test.go                 |  46 ++---
 internal/archiver/archiver_unix_test.go            |   4 +-
 internal/archiver/exclude_test.go                  |   8 +-
 internal/archiver/file_saver.go                    |   2 +-
 internal/archiver/file_saver_test.go               |   4 +-
 internal/archiver/scanner_test.go                  |   6 +-
 internal/archiver/testing.go                       |   4 +-
 internal/archiver/testing_test.go                  |   2 +-
 internal/archiver/tree.go                          |   6 +-
 internal/archiver/tree_test.go                     |  12 +-
 internal/backend/cache/file.go                     |  15 +-
 internal/bloblru/cache.go                          |  12 +-
 internal/bloblru/cache_test.go                     |  14 +-
 internal/checker/checker.go                        |  15 +-
 internal/checker/checker_test.go                   |  86 ++++----
 internal/checker/testing.go                        |   6 +-
 internal/data/find.go                              |   3 +-
 internal/data/find_test.go                         |  10 +-
 internal/data/node.go                              |  25 +--
 internal/data/node_test.go                         |   2 +-
 internal/data/testing.go                           |   6 +-
 internal/data/tree.go                              |   2 +-
 internal/data/tree_stream.go                       |  11 +-
 internal/data/tree_test.go                         |   2 +-
 internal/dump/common.go                            |   2 +-
 internal/dump/common_test.go                       |   2 +-
 internal/fs/file_unix_test.go                      |   2 +-
 internal/fs/fs_local.go                            |  33 +--
 internal/fs/fs_local_test.go                       |   8 +-
 internal/fs/fs_local_vss.go                        |  27 +--
 internal/fs/fs_reader.go                           |  36 ++--
 internal/fs/fs_reader_command.go                   |  14 +-
 internal/fs/node_test.go                           |   4 +-
 internal/fs/node_unix_test.go                      |   2 +-
 internal/fs/node_windows_test.go                   |   2 +-
 internal/fs/vss.go                                 |  26 +--
 internal/fs/vss_windows.go                         |  92 ++++-----
 internal/fuse/file.go                              |   4 +-
 internal/fuse/fuse_test.go                         |   4 +-
 internal/fuse/snapshots_dirstruct.go               |   3 +-
 internal/repository/checker.go                     |  38 ++--
 internal/repository/checker_test.go                | 224 +++++++++++++++++++++
 internal/{ => repository}/crypto/buffer.go         |   0
 internal/{ => repository}/crypto/crypto.go         |   0
 .../{ => repository}/crypto/crypto_int_test.go     |   0
 internal/{ => repository}/crypto/crypto_test.go    |   2 +-
 internal/{ => repository}/crypto/doc.go            |   0
 internal/{ => repository}/crypto/kdf.go            |   0
 internal/{ => repository}/crypto/kdf_test.go       |   0
 internal/repository/debug.go                       |  19 +-
 internal/repository/fuzz_test.go                   |   2 +-
 internal/repository/index/associated_data.go       |   7 +-
 internal/repository/index/associated_data_test.go  |  27 +--
 internal/repository/index/index.go                 |  45 +++--
 internal/repository/index/index_internal_test.go   |   4 +-
 internal/repository/index/index_parallel_test.go   |   3 +-
 internal/repository/index/index_test.go            |  87 ++++----
 internal/repository/index/master_index.go          |  67 +++---
 internal/repository/index/master_index_test.go     | 210 +++++++++----------
 internal/repository/index_list.go                  |   2 +-
 internal/repository/index_list_test.go             |   6 +-
 internal/repository/index_testutil_test.go         |  18 ++
 internal/repository/key.go                         |  14 +-
 internal/repository/lock.go                        |  84 ++++----
 .../{restic/lock.go => repository/lock_file.go}    | 217 ++++++++------------
 .../lock_test.go => repository/lock_file_test.go}  | 123 +++++------
 .../lock_unix.go => repository/lock_file_unix.go}  |  35 ++--
 .../lock_file_windows.go}                          |  10 +-
 internal/repository/lock_test.go                   |  27 ++-
 internal/repository/pack/blob.go                   |  36 ++++
 internal/repository/pack/blobs.go                  |  15 ++
 internal/repository/pack/blobs_test.go             |  24 +++
 internal/repository/pack/pack.go                   |  39 ++--
 internal/repository/pack/pack_internal_test.go     |   4 +-
 internal/repository/pack/pack_test.go              |   2 +-
 internal/repository/pack/packedblob.go             |  25 +++
 internal/repository/packer_manager.go              |   2 +-
 internal/repository/packer_manager_test.go         |   2 +-
 internal/repository/prune.go                       | 113 +++++++----
 internal/repository/prune_internal_test.go         |   4 +-
 internal/repository/prune_test.go                  |  14 +-
 internal/repository/repack.go                      |  21 +-
 internal/repository/repack_test.go                 |  64 +++---
 internal/repository/repair_index.go                |   4 +-
 internal/repository/repair_index_test.go           |   2 +-
 internal/repository/repair_pack.go                 |  13 +-
 internal/repository/repair_pack_test.go            |  27 ++-
 internal/repository/repository.go                  | 135 ++++++++-----
 internal/repository/repository_internal_test.go    |  43 ++--
 internal/repository/repository_test.go             |  41 ++--
 internal/repository/testing.go                     |  19 +-
 internal/repository/warmup.go                      |   8 +-
 internal/restic/blob.go                            |  52 ++---
 internal/restic/blob_test.go                       |  19 --
 internal/restic/parallel.go                        |   3 +-
 internal/restic/parallel_test.go                   |  14 +-
 internal/restic/progress.go                        |  28 +++
 internal/restic/progress_test.go                   |  18 ++
 internal/restic/repository.go                      |  33 ++-
 internal/restic/uid_unix.go                        |  25 +++
 internal/restic/uid_windows.go                     |  10 +
 internal/restorer/filerestorer.go                  |  43 ++--
 internal/restorer/filerestorer_test.go             | 104 +++++++---
 internal/restorer/hardlinks_index.go               |  18 +-
 internal/restorer/restorer.go                      |   7 +-
 internal/restorer/restorer_test.go                 |  22 +-
 internal/restorer/restorer_unix_test.go            |   5 +-
 internal/test/helpers.go                           |  29 +--
 internal/test/vars.go                              |   7 +-
 internal/ui/backup/json.go                         |  30 +--
 internal/ui/backup/progress.go                     |   6 +-
 internal/ui/backup/progress_test.go                |   6 +-
 internal/ui/backup/text.go                         |  26 +--
 internal/ui/message.go                             |  64 ------
 internal/ui/progress.go                            |  78 -------
 internal/ui/progress/counter.go                    |  16 +-
 internal/ui/progress/counter_test.go               |   8 -
 internal/ui/progress/printer.go                    |  80 ++------
 internal/ui/progress/terminal.go                   | 109 ++++++++++
 internal/ui/restore/json.go                        |   2 +-
 internal/ui/restore/progress.go                    |   6 +-
 internal/ui/restore/progress_test.go               |   6 +-
 internal/ui/restore/text.go                        |   2 +-
 internal/ui/stats/progress.go                      |  94 +++++++++
 internal/ui/stats/progress_test.go                 |  44 ++++
 internal/ui/terminal.go                            |   2 +-
 internal/ui/termstatus/status.go                   |  89 ++++----
 internal/ui/termstatus/status_test.go              |  32 +--
 internal/walker/testing.go                         |   1 -
 183 files changed, 2417 insertions(+), 1871 deletions(-)
 create mode 100644 changelog/unreleased/issue-21866
 create mode 100644 changelog/unreleased/issue-3129
 create mode 100644 changelog/unreleased/pull-21876
 create mode 100644 changelog/unreleased/pull-21879
 create mode 100644 internal/repository/checker_test.go
 rename internal/{ => repository}/crypto/buffer.go (100%)
 rename internal/{ => repository}/crypto/crypto.go (100%)
 rename internal/{ => repository}/crypto/crypto_int_test.go (100%)
 rename internal/{ => repository}/crypto/crypto_test.go (99%)
 rename internal/{ => repository}/crypto/doc.go (100%)
 rename internal/{ => repository}/crypto/kdf.go (100%)
 rename internal/{ => repository}/crypto/kdf_test.go (100%)
 create mode 100644 internal/repository/index_testutil_test.go
 rename internal/{restic/lock.go => repository/lock_file.go} (64%)
 rename internal/{restic/lock_test.go => repository/lock_file_test.go} (57%)
 rename internal/{restic/lock_unix.go => repository/lock_file_unix.go} (52%)
 rename internal/{restic/lock_windows.go => repository/lock_file_windows.go} (66%)
 create mode 100644 internal/repository/pack/blob.go
 create mode 100644 internal/repository/pack/blobs.go
 create mode 100644 internal/repository/pack/blobs_test.go
 create mode 100644 internal/repository/pack/packedblob.go
 create mode 100644 internal/restic/progress.go
 create mode 100644 internal/restic/progress_test.go
 create mode 100644 internal/restic/uid_unix.go
 create mode 100644 internal/restic/uid_windows.go
 delete mode 100644 internal/ui/message.go
 delete mode 100644 internal/ui/progress.go
 create mode 100644 internal/ui/progress/terminal.go
 create mode 100644 internal/ui/stats/progress.go
 create mode 100644 internal/ui/stats/progress_test.go
 delete mode 100644 internal/walker/testing.go
- Status: updated existing repo

## MasterDnsVPN networking reference
- URL: https://github.com/masterking32/MasterDnsVPN.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/networking/masterdnsvpn
Cloning into '/root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/networking/masterdnsvpn'...
- Status: cloned or attempted clone

## AgentsView local-first agent analytics
- URL: https://github.com/kenn-io/agentsview.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/observability/agentsview
From https://github.com/kenn-io/agentsview
   293342a..6589c9f  main       -> origin/main
Updating 293342a..6589c9f
Fast-forward
 .github/workflows/ci.yml                           |   19 +
 .gitignore                                         |    2 +
 AGENTS.md                                          |   16 +-
 Makefile                                           |    4 +-
 README.md                                          |   41 +-
 SECURITY.md                                        |  275 ++--
 cmd/agentsview/cli.go                              |    1 +
 cmd/agentsview/managed_caddy.go                    |   57 +-
 cmd/agentsview/managed_caddy_test.go               |   42 +
 cmd/agentsview/parse_diff.go                       |  492 ++++++
 cmd/agentsview/parse_diff_test.go                  |  712 +++++++++
 docs/huma-api-routes.md                            |   14 +-
 frontend/AGENTS.md                                 |   24 +
 frontend/package-lock.json                         | 1601 +++++++++++++++-----
 frontend/package.json                              |   17 +-
 .../src/lib/api/client-markdown-export.test.ts     |    2 +-
 frontend/src/lib/api/client.test.ts                |    2 +-
 frontend/src/lib/api/generated/index.ts            |    5 +
 .../api/generated/models/DbSkillAgentBreakdown.ts  |    9 +
 .../generated/models/DbSkillProjectBreakdown.ts    |    9 +
 .../lib/api/generated/models/DbSkillTrendEntry.ts  |    9 +
 .../src/lib/api/generated/models/DbSkillUsage.ts   |   14 +
 .../generated/models/DbSkillsAnalyticsResponse.ts  |   11 +
 .../lib/api/generated/models/SettingsResponse.ts   |    2 +-
 .../lib/api/generated/services/AnalyticsService.ts |  107 ++
 frontend/src/lib/api/types/analytics.ts            |   32 +
 .../lib/components/analytics/AnalyticsPage.svelte  |    5 +
 .../components/analytics/HourOfWeekHeatmap.svelte  |   20 +-
 .../components/analytics/HourOfWeekHeatmap.test.ts |   93 ++
 .../lib/components/analytics/TopSessions.test.ts   |    2 +-
 .../src/lib/components/analytics/TopSkills.svelte  |  465 ++++++
 .../src/lib/components/analytics/TopSkills.test.ts |  149 ++
 .../command-palette/CommandPalette.svelte          |   10 +-
 .../command-palette/CommandPalette.test.ts         |   50 +-
 .../components/content/CallRow_CallGroup.test.ts   |    2 +-
 .../content/CompactBoundaryDivider.test.ts         |    2 +-
 .../lib/components/content/MessageContent.test.ts  |    2 +-
 .../lib/components/content/SubagentInline.test.ts  |    2 +-
 .../src/lib/components/content/ToolBlock.test.ts   |   26 +-
 .../src/lib/components/layout/AppHeader.svelte     |   31 +
 .../src/lib/components/layout/AppHeader.test.ts    |   56 +-
 .../components/layout/SessionBreadcrumb.test.ts    |    2 +-
 .../src/lib/components/layout/StatusBar.test.ts    |    2 +-
 .../components/layout/ThreeColumnLayout.test.ts    |    2 +-
 .../lib/components/layout/sidebar-width.test.ts    |    2 +-
 .../lib/components/settings/SettingsPage.svelte    |    4 +-
 .../lib/components/settings/SettingsPage.test.ts   |   88 ++
 .../settings/WorktreeMappingSettings.svelte        |   14 +-
 .../settings/WorktreeMappingSettings.test.ts       |   48 +
 .../src/lib/components/shared/CopyButton.test.ts   |    2 +-
 .../components/shared/dateRangeSelector.test.ts    |    2 +-
 .../src/lib/components/sidebar/SessionItem.svelte  |   26 +-
 .../src/lib/components/sidebar/SessionList.test.ts |   42 +-
 .../components/sidebar/session-list-utils.test.ts  |    2 +-
 .../components/system/SystemBoundaryCard.test.ts   |    2 +-
 .../src/lib/components/trends/TrendsPage.test.ts   |    2 +-
 frontend/src/lib/stores/analytics.svelte.ts        |   26 +
 frontend/src/lib/stores/analytics.test.ts          |   26 +-
 frontend/src/lib/stores/events.svelte.ts           |   15 +
 frontend/src/lib/stores/events.test.ts             |   20 +-
 frontend/src/lib/stores/insights.test.ts           |    2 +-
 frontend/src/lib/stores/messages.test.ts           |    2 +-
 frontend/src/lib/stores/pins.test.ts               |    2 +-
 frontend/src/lib/stores/router.test.ts             |    2 +-
 frontend/src/lib/stores/search.test.ts             |    2 +-
 frontend/src/lib/stores/sessionActivity.test.ts    |    2 +-
 frontend/src/lib/stores/sessions.test.ts           |    2 +-
 frontend/src/lib/stores/settings.svelte.ts         |    6 +
 frontend/src/lib/stores/settings.test.ts           |   20 +
 frontend/src/lib/stores/starred.test.ts            |    2 +-
 frontend/src/lib/stores/sync.svelte.ts             |   14 +-
 frontend/src/lib/stores/sync.test.ts               |   57 +-
 frontend/src/lib/stores/trends.test.ts             |    2 +-
 frontend/src/lib/stores/ui.test.ts                 |    2 +-
 frontend/src/lib/stores/usage.test.ts              |    2 +-
 frontend/src/lib/utils/agents.test.ts              |    2 +-
 frontend/src/lib/utils/cache.test.ts               |    2 +-
 frontend/src/lib/utils/categoryAttribution.test.ts |    2 +-
 frontend/src/lib/utils/clipboard.test.ts           |    2 +-
 frontend/src/lib/utils/content-parser.test.ts      |   11 +-
 frontend/src/lib/utils/content-parser.ts           |    6 +-
 frontend/src/lib/utils/copy-message.test.ts        |    2 +-
 frontend/src/lib/utils/csv-export.test.ts          |    2 +-
 frontend/src/lib/utils/dates.test.ts               |    2 +-
 frontend/src/lib/utils/display-items.test.ts       |    2 +-
 frontend/src/lib/utils/duration.test.ts            |    2 +-
 frontend/src/lib/utils/format.test.ts              |    2 +-
 frontend/src/lib/utils/health.test.ts              |    2 +-
 frontend/src/lib/utils/highlight.test.ts           |    2 +-
 frontend/src/lib/utils/keyboard.test.ts            |    2 +-
 frontend/src/lib/utils/markdown.test.ts            |    2 +-
 frontend/src/lib/utils/messages.test.ts            |    2 +-
 frontend/src/lib/utils/model.test.ts               |    2 +-
 frontend/src/lib/utils/poll.test.ts                |    2 +-
 frontend/src/lib/utils/projectColor.test.ts        |    2 +-
 frontend/src/lib/utils/resume.test.ts              |    2 +-
 frontend/src/lib/utils/tool-params.test.ts         |   13 +-
 frontend/src/lib/utils/tool-params.ts              |    9 +
 frontend/src/lib/utils/toolDisplay.test.ts         |    2 +-
 frontend/src/lib/utils/transcript-mode.test.ts     |    2 +-
 frontend/src/lib/utils/treemap.test.ts             |    2 +-
 frontend/src/lib/utils/usageSavings.test.ts        |    2 +-
 .../lib/virtual/createVirtualizer.cache.test.ts    |    2 +-
 frontend/src/lib/virtual/createVirtualizer.test.ts |    2 +-
 frontend/src/vite-env.d.ts                         |    2 +-
 frontend/src/vitest-setup.test.ts                  |   63 +
 frontend/src/vitest-setup.ts                       |   53 +
 frontend/vite.config.ts                            |   16 +-
 internal/db/analytics.go                           |  299 ++++
 internal/db/analytics_test.go                      |  161 ++
 internal/db/db.go                                  |   22 +-
 internal/db/db_test.go                             |   76 +
 internal/db/messages.go                            |  247 ++-
 internal/db/messages_test.go                       |   61 +
 internal/db/store.go                               |    1 +
 internal/db/store_contract_test.go                 |   11 +
 internal/duckdb/analytics_usage.go                 |   51 +
 internal/duckdb/store_contract_test.go             |    7 +
 internal/duckdb/sync_test.go                       |    1 +
 internal/parser/antigravity.go                     |  383 ++++-
 internal/parser/antigravity_fuzz_test.go           |   39 +-
 internal/parser/antigravity_test.go                |  713 ++++++++-
 internal/parser/claude.go                          |  191 ++-
 internal/parser/claude_parser_test.go              |   84 +
 internal/parser/content.go                         |   15 +-
 internal/parser/cursor.go                          |   92 +-
 internal/parser/cursor_test.go                     |   47 +
 internal/parser/gptme.go                           |  293 ++++
 internal/parser/gptme_test.go                      |   99 ++
 internal/parser/pi.go                              |    1 +
 internal/parser/pi_test.go                         |    3 +
 internal/parser/taxonomy.go                        |    2 +
 internal/parser/taxonomy_test.go                   |    3 +
 .../conversation.jsonl                             |    7 +
 internal/parser/timestamp.go                       |    1 +
 internal/parser/types.go                           |   12 +
 internal/parser/types_test.go                      |   31 +
 internal/postgres/analytics.go                     |  121 ++
 internal/postgres/analytics_unit_test.go           |   52 +
 internal/postgres/push.go                          |   60 +
 internal/server/analytics_test.go                  |   32 +
 internal/server/export_markdown.go                 |    9 +-
 internal/server/export_test.go                     |   55 +
 internal/server/huma_routes_analytics.go           |   16 +
 internal/server/huma_routes_settings.go            |    1 +
 internal/server/middleware_test.go                 |   63 +-
 internal/server/server.go                          |   82 +-
 internal/server/session_mgmt_test.go               |   96 ++
 internal/server/settings.go                        |    1 +
 internal/server/starred_test.go                    |   78 +
 internal/sync/engine.go                            |  170 ++-
 internal/sync/engine_integration_test.go           |   43 +
 internal/sync/parsediff.go                         |  664 ++++++++
 internal/sync/parsediff_compare.go                 | 1220 +++++++++++++++
 internal/sync/parsediff_compare_test.go            | 1559 +++++++++++++++++++
 internal/sync/parsediff_integration_test.go        | 1037 +++++++++++++
 internal/sync/parsediff_report.go                  |  188 +++
 157 files changed, 12723 insertions(+), 880 deletions(-)
 create mode 100644 cmd/agentsview/parse_diff.go
 create mode 100644 cmd/agentsview/parse_diff_test.go
 create mode 100644 frontend/AGENTS.md
 create mode 100644 frontend/src/lib/api/generated/models/DbSkillAgentBreakdown.ts
 create mode 100644 frontend/src/lib/api/generated/models/DbSkillProjectBreakdown.ts
 create mode 100644 frontend/src/lib/api/generated/models/DbSkillTrendEntry.ts
 create mode 100644 frontend/src/lib/api/generated/models/DbSkillUsage.ts
 create mode 100644 frontend/src/lib/api/generated/models/DbSkillsAnalyticsResponse.ts
 create mode 100644 frontend/src/lib/components/analytics/HourOfWeekHeatmap.test.ts
 create mode 100644 frontend/src/lib/components/analytics/TopSkills.svelte
 create mode 100644 frontend/src/lib/components/analytics/TopSkills.test.ts
 create mode 100644 frontend/src/lib/components/settings/SettingsPage.test.ts
 create mode 100644 frontend/src/lib/components/settings/WorktreeMappingSettings.test.ts
 create mode 100644 frontend/src/vitest-setup.test.ts
 create mode 100644 frontend/src/vitest-setup.ts
 create mode 100644 internal/parser/gptme.go
 create mode 100644 internal/parser/gptme_test.go
 create mode 100644 internal/parser/testdata/gptme/2026-06-13-write-hello-world/conversation.jsonl
 create mode 100644 internal/server/session_mgmt_test.go
 create mode 100644 internal/server/starred_test.go
 create mode 100644 internal/sync/parsediff.go
 create mode 100644 internal/sync/parsediff_compare.go
 create mode 100644 internal/sync/parsediff_compare_test.go
 create mode 100644 internal/sync/parsediff_integration_test.go
 create mode 100644 internal/sync/parsediff_report.go
- Status: updated existing repo

## SIA self-improving AI framework
- URL: https://github.com/hexo-ai/sia.git
- Path: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/self-improvement/hexo-ai-sia
Already up to date.
- Status: updated existing repo


# EMBIZ Adaptation Requirement

These repos are source material only. Do not install or run them blindly.

Each source must be converted into EMBIZ-specific doctrine before use:

- Mattermost → Slack/Mattermost collaboration protocol for visible agent teamwork
- CRM-AI-Analysis → structured job data, reporting, medallion-style customer/job state architecture
- agent-skills / pm-skills / superpowers → EMBIZ-specific skills with approval gates and evidence checks
- SkillSpector → scan agent skills before adoption
- Tolaria → markdown knowledge-base management pattern
- Restic → backup and recovery protocol
- AgentsView → agent observability and session analytics model
- SIA → benchmark-driven recursive self-improvement protocol
- MasterDnsVPN → networking reference only; do not deploy unless explicitly approved
- Ink/Stitch → embroidery digitization runtime/reference layer

# Required Next Build

Create:

1. EMBIZ_SELF_HEALING_AND_RECURSIVE_OPTIMIZATION_PROTOCOL.md
2. EMBIZ_AGENT_TRAINING_LOOP_PROTOCOL.md
3. EMBIZ_IMPORTED_SKILLS_ADAPTATION_POLICY.md
4. EMBIZ_KNOWLEDGE_BASE_SOURCE_REGISTRY.md
5. EMBIZ_AGENT_OBSERVABILITY_PROTOCOL.md
6. EMBIZ_BACKUP_AND_ROLLBACK_PROTOCOL.md
7. EMBIZ_COLLABORATION_PROTOCOL.md

