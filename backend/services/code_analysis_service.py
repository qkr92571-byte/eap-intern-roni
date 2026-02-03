"""
코드 분석 서비스
- AST 파싱을 통한 코드 구조 분석
- 순환 복잡도 계산
- 코드 메트릭 수집
- 중복 코드 감지
- 의존성 분석
"""

import ast
import re
from typing import List, Dict, Optional, Set, Tuple
from pathlib import Path
from collections import defaultdict
import json


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    current = Path(__file__).parent.parent.parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'backend').exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent.parent


class PythonCodeAnalyzer:
    """Python 코드 분석기"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.project_root = get_project_root()
        self.full_path = self.project_root / file_path
        self.ast_tree: Optional[ast.AST] = None
        self.source_code: str = ""
    
    def load_code(self) -> bool:
        """코드 파일 로드"""
        try:
            if not self.full_path.exists():
                return False
            self.source_code = self.full_path.read_text(encoding='utf-8')
            self.ast_tree = ast.parse(self.source_code, filename=self.file_path)
            return True
        except SyntaxError as e:
            print(f"⚠️  구문 오류 ({self.file_path}): {str(e)}")
            return False
        except Exception as e:
            print(f"⚠️  파일 로드 실패 ({self.file_path}): {str(e)}")
            return False
    
    def get_metrics(self) -> Dict:
        """코드 메트릭 수집"""
        if not self.ast_tree:
            return {}
        
        metrics = {
            'total_lines': len(self.source_code.splitlines()),
            'code_lines': 0,
            'blank_lines': 0,
            'comment_lines': 0,
            'functions': [],
            'classes': [],
            'imports': [],
            'complexity': 0,
            'max_function_complexity': 0
        }
        
        # 라인 카운트
        for line in self.source_code.splitlines():
            stripped = line.strip()
            if not stripped:
                metrics['blank_lines'] += 1
            elif stripped.startswith('#'):
                metrics['comment_lines'] += 1
            else:
                metrics['code_lines'] += 1
        
        # AST 순회
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._analyze_function(node)
                metrics['functions'].append(func_info)
                metrics['complexity'] += func_info['complexity']
                metrics['max_function_complexity'] = max(
                    metrics['max_function_complexity'],
                    func_info['complexity']
                )
            elif isinstance(node, ast.ClassDef):
                class_info = self._analyze_class(node)
                metrics['classes'].append(class_info)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._analyze_import(node)
                metrics['imports'].append(import_info)
        
        metrics['function_count'] = len(metrics['functions'])
        metrics['class_count'] = len(metrics['classes'])
        metrics['import_count'] = len(metrics['imports'])
        
        return metrics
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict:
        """함수 분석"""
        complexity = self._calculate_complexity(node)
        lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
        
        return {
            'name': node.name,
            'line': node.lineno,
            'lines': lines,
            'complexity': complexity,
            'parameters': len(node.args.args),
            'decorators': [ast.unparse(d) if hasattr(ast, 'unparse') else '' for d in node.decorator_list]
        }
    
    def _analyze_class(self, node: ast.ClassDef) -> Dict:
        """클래스 분석"""
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        
        return {
            'name': node.name,
            'line': node.lineno,
            'methods': len(methods),
            'method_names': methods
        }
    
    def _analyze_import(self, node: ast.Import) -> Dict:
        """임포트 분석"""
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        else:  # ImportFrom
            names = [alias.name for alias in node.names] if node.names else []
            module = node.module or ''
            return {
                'type': 'from',
                'module': module,
                'names': names,
                'line': node.lineno
            }
        
        return {
            'type': 'import',
            'names': names,
            'line': node.lineno
        }
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """순환 복잡도 계산 (간단한 버전)"""
        complexity = 1  # 기본 복잡도
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def find_duplicate_code(self, min_lines: int = 5) -> List[Dict]:
        """중복 코드 감지 (간단한 버전)"""
        if not self.source_code:
            return []
        
        lines = self.source_code.splitlines()
        duplicates = []
        seen_blocks = {}
        
        # 슬라이딩 윈도우로 코드 블록 비교
        for i in range(len(lines) - min_lines + 1):
            block = '\n'.join(lines[i:i + min_lines])
            block_hash = hash(block.strip())
            
            if block_hash in seen_blocks:
                # 중복 발견
                original = seen_blocks[block_hash]
                if original['file'] != self.file_path or abs(original['line'] - i) > min_lines:
                    duplicates.append({
                        'file': self.file_path,
                        'start_line': i + 1,
                        'end_line': i + min_lines,
                        'duplicate_of': {
                            'file': original['file'],
                            'start_line': original['line'] + 1,
                            'end_line': original['line'] + min_lines
                        }
                    })
            else:
                seen_blocks[block_hash] = {
                    'file': self.file_path,
                    'line': i
                }
        
        return duplicates
    
    def analyze_dependencies(self) -> Dict:
        """의존성 분석"""
        if not self.ast_tree:
            return {}
        
        dependencies = {
            'imports': [],
            'from_imports': [],
            'external_modules': set(),
            'internal_modules': set()
        }
        
        project_root = get_project_root()
        
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split('.')[0]
                    dependencies['imports'].append(module)
                    if self._is_external_module(module, project_root):
                        dependencies['external_modules'].add(module)
                    else:
                        dependencies['internal_modules'].add(module)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split('.')[0]
                    dependencies['from_imports'].append(node.module)
                    if self._is_external_module(module, project_root):
                        dependencies['external_modules'].add(module)
                    else:
                        dependencies['internal_modules'].add(module)
        
        dependencies['external_modules'] = list(dependencies['external_modules'])
        dependencies['internal_modules'] = list(dependencies['internal_modules'])
        
        return dependencies
    
    def _is_external_module(self, module: str, project_root: Path) -> bool:
        """외부 모듈인지 확인"""
        # 표준 라이브러리 또는 외부 패키지
        if module in ['os', 'sys', 'json', 'datetime', 'pathlib', 'typing', 'collections']:
            return True
        
        # 프로젝트 내부 모듈 확인
        backend_path = project_root / 'backend'
        if (backend_path / module).exists() or (backend_path / f'{module}.py').exists():
            return False
        
        return True


class TypeScriptCodeAnalyzer:
    """TypeScript/JavaScript 코드 분석기 (간단한 버전)"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.project_root = get_project_root()
        self.full_path = self.project_root / file_path
        self.source_code: str = ""
    
    def load_code(self) -> bool:
        """코드 파일 로드"""
        try:
            if not self.full_path.exists():
                return False
            self.source_code = self.full_path.read_text(encoding='utf-8')
            return True
        except Exception as e:
            print(f"⚠️  파일 로드 실패 ({self.file_path}): {str(e)}")
            return False
    
    def get_metrics(self) -> Dict:
        """코드 메트릭 수집"""
        if not self.source_code:
            return {}
        
        metrics = {
            'total_lines': len(self.source_code.splitlines()),
            'code_lines': 0,
            'blank_lines': 0,
            'comment_lines': 0,
            'functions': [],
            'classes': [],
            'imports': []
        }
        
        lines = self.source_code.splitlines()
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics['blank_lines'] += 1
            elif stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                metrics['comment_lines'] += 1
            else:
                metrics['code_lines'] += 1
        
        # 함수 추출 (간단한 정규식 기반)
        function_pattern = r'(?:export\s+)?(?:async\s+)?(?:function\s+)?(\w+)\s*[=:]?\s*\([^)]*\)\s*[:{=]'
        functions = re.finditer(function_pattern, self.source_code)
        for match in functions:
            metrics['functions'].append({
                'name': match.group(1),
                'line': self.source_code[:match.start()].count('\n') + 1
            })
        
        # 클래스 추출
        class_pattern = r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)'
        classes = re.finditer(class_pattern, self.source_code)
        for match in classes:
            metrics['classes'].append({
                'name': match.group(1),
                'line': self.source_code[:match.start()].count('\n') + 1
            })
        
        # 임포트 추출
        import_pattern = r'import\s+(?:.*?\s+from\s+)?[\'"]([^\'"]+)[\'"]'
        imports = re.finditer(import_pattern, self.source_code)
        for match in imports:
            metrics['imports'].append({
                'module': match.group(1),
                'line': self.source_code[:match.start()].count('\n') + 1
            })
        
        metrics['function_count'] = len(metrics['functions'])
        metrics['class_count'] = len(metrics['classes'])
        metrics['import_count'] = len(metrics['imports'])
        
        return metrics


def analyze_file(file_path: str) -> Dict:
    """
    파일 분석
    
    Args:
        file_path: 파일 경로
    
    Returns:
        분석 결과 딕셔너리
    """
    if file_path.endswith('.py'):
        analyzer = PythonCodeAnalyzer(file_path)
        if analyzer.load_code():
            return {
                'file': file_path,
                'type': 'python',
                'metrics': analyzer.get_metrics(),
                'dependencies': analyzer.analyze_dependencies(),
                'duplicates': analyzer.find_duplicate_code()
            }
    elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
        analyzer = TypeScriptCodeAnalyzer(file_path)
        if analyzer.load_code():
            return {
                'file': file_path,
                'type': 'typescript' if file_path.endswith(('.ts', '.tsx')) else 'javascript',
                'metrics': analyzer.get_metrics(),
                'dependencies': {},  # TypeScript 의존성 분석은 복잡하므로 생략
                'duplicates': []  # TypeScript 중복 감지는 복잡하므로 생략
            }
    
    return {
        'file': file_path,
        'type': 'unknown',
        'error': '지원하지 않는 파일 형식'
    }


def analyze_directory(directory: str, recursive: bool = True) -> Dict[str, Dict]:
    """
    디렉토리 내 모든 파일 분석
    
    Args:
        directory: 디렉토리 경로
        recursive: 재귀적으로 분석할지 여부
    
    Returns:
        파일별 분석 결과 딕셔너리
    """
    project_root = get_project_root()
    target_dir = project_root / directory
    
    if not target_dir.exists() or not target_dir.is_dir():
        return {}
    
    results = {}
    
    # Python 파일
    pattern = '**/*.py' if recursive else '*.py'
    for py_file in target_dir.glob(pattern):
        rel_path = str(py_file.relative_to(project_root))
        analysis = analyze_file(rel_path)
        if analysis:
            results[rel_path] = analysis
    
    # TypeScript/JavaScript 파일
    for ext in ['*.ts', '*.tsx', '*.js', '*.jsx']:
        pattern = f'**/{ext}' if recursive else ext
        for js_file in target_dir.glob(pattern):
            rel_path = str(js_file.relative_to(project_root))
            analysis = analyze_file(rel_path)
            if analysis:
                results[rel_path] = analysis
    
    return results


def aggregate_metrics(analyses: Dict[str, Dict]) -> Dict:
    """
    분석 결과 집계
    
    Args:
        analyses: 파일별 분석 결과
    
    Returns:
        집계된 메트릭
    """
    total_files = len(analyses)
    total_lines = 0
    total_functions = 0
    total_classes = 0
    total_complexity = 0
    max_complexity = 0
    
    for analysis in analyses.values():
        metrics = analysis.get('metrics', {})
        total_lines += metrics.get('total_lines', 0)
        total_functions += metrics.get('function_count', 0)
        total_classes += metrics.get('class_count', 0)
        total_complexity += metrics.get('complexity', 0)
        max_complexity = max(max_complexity, metrics.get('max_function_complexity', 0))
    
    return {
        'total_files': total_files,
        'total_lines': total_lines,
        'total_functions': total_functions,
        'total_classes': total_classes,
        'average_complexity': total_complexity / total_functions if total_functions > 0 else 0,
        'max_complexity': max_complexity
    }

