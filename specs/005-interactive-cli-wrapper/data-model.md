# Data Model: Interactive CLI Wrapper

## SelectableBookEntry

Represents one supported source file shown in the interactive picker.

Fields:
- `index`: numeric selection index shown to the user
- `path`: full resolved path to the source file
- `label`: user-facing filename label

## InteractiveRunRequest

Represents one confirmed interactive parser request.

Fields:
- `input_path`: selected source file
- `strategy`: selected parser strategy
- `config_path`: chosen config file path
- `output_dir`: chosen output directory
- `json_output`: whether JSON output is enabled

## ExecutionPreview

Represents the final summary shown before the wrapper runs the parser.

Fields:
- `input_path`
- `strategy`
- `config_path`
- `output_dir`
- `json_output`

Role:
- make the final execution explicit
- give the user one confirmation boundary before parser side effects occur
