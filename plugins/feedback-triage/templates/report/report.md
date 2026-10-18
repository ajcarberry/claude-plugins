{{! One standalone Markdown report per ticket, pasteable into Jira, Linear, GitHub, … }}
{{! Rendered by ft.py render — never hand-written. A #x … /x pair keeps a section only when x is set. }}
# {{headline}}

{{intro}}

**Type:** {{type_label}} · **Status:** {{status}}{{repro_part}} · **Reported by:** {{reporters}}

## What's happening

{{what}}

## What we found

- {{findings[]}}

{{#fix}}
## Proposed fix

{{fix}}

{{fix_link}}

{{handoff}}
{{/fix}}

## Sources

- {{sources[]}}
