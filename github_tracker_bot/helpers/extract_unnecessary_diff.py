import re

non_code_patterns = [
    r'^yarn\.lock$', 
    r'^package-lock\.json$', 
    r'^pnpm-lock\.yaml$',
    r'^pipfile\.lock$', 
    r'^\.gitignore$', 
    r'^\.editorconfig$', 
    r'^\.eslintignore$', 
    r'^\.eslintrc\.json$', 
    r'^\.prettierrc$', 
    r'^\.prettierrc\.json$', 
    r'^\.prettierrc\.yaml$', 
    r'^\.stylelintrc$', 
    r'^\.stylelintrc\.json$', 
    r'^\.stylelintrc\.yaml$', 
    r'^\.browserslistrc$', 
    r'^\.npmrc$', 
    r'^\.yarnrc$', 
    r'^\.nvmrc$', 
    r'^\.env$', 
    r'^\.env\.example$', 
    r'^CONTRIBUTING\.md$', 
    r'^CHANGELOG\.md$', 
    r'^Dockerfile$', 
    r'^Jenkinsfile$', 
    r'^\.travis\.yml$', 
    r'^\.circleci/config\.yml$', 
    r'^Makefile$', 
    r'.*\.(png|jpg|gif|svg)$', 
    r'.*\.(pdf|docx)$', 
    r'.*\.log$', 
    r'.*\.csv$', 
    r'.*\.json$', 
    r'^node_modules/.*', 
    r'^vendor/.*', 
    r'^dist/.*', 
    r'^build/.*', 
    r'^target/.*', 
    r'^\.DS_Store$', 
    r'^thumbs\.db$', 
    r'^\.vscode/.*', 
    r'^\.idea/.*',
    r'^\.github/workflows/.*', 
    r'^azure-pipelines\.yml$', 
    r'^bitbucket-pipelines\.yml$', 
    r'^.gitlab-ci\.yml$', 
    r'^Cargo\.toml$', 
    r'^Cargo\.lock$', 
    r'^tsconfig\.json$', 
    r'^jsconfig\.json$', 
    r'^tslint\.json$', 
    r'^jest\.config\.js$', 
    r'^babel\.config\.js$', 
    r'^webpack\.config\.js$', 
    r'^rollup\.config\.js$', 
    r'^Pipfile$', 
    r'^requirements\.txt$', 
    r'^pyproject\.toml$', 
    r'^tox\.ini$', 
]

def is_non_code_file(file_path):
    for pattern in non_code_patterns:
        if re.match(pattern, file_path):
            return True
    return False

def extract_file_path(diff_data):
    pattern = r'diff --git a\/(.+?) b\/(.+?)\n'
    match = re.search(pattern, diff_data)
    if match:
        return match.group(1)
    return None

def process_diff(diff_data):
    file_path = extract_file_path(diff_data)
    if file_path:
        if is_non_code_file(file_path):
            return True
        else:
            return False
    else:
        return True
    

def filter_diffs(diff_text):
    combined_pattern = re.compile("|".join(non_code_patterns))

    diffs = diff_text.strip().split('diff --git')
    filtered_diffs = []

    for diff in diffs:
        if not diff.strip():
            continue
        
        path_match = re.search(r'a/(.*) b/(.*)', diff)
        if not path_match:
            continue

        file_path_a = path_match.group(1)
        file_path_b = path_match.group(2)
        
        if not (combined_pattern.search(file_path_a) or combined_pattern.search(file_path_b)):
            filtered_diffs.append('diff --git' + diff)

    return '\n '.join(filtered_diffs)


