#!/usr/bin/env python3
"""
Python 2 Syntax Analyzer - Detects Python 2 specific syntax and constructs.
This script scans Python files for Python 2-specific code patterns.
"""

import os
import re
import sys
import ast
from collections import defaultdict

class Python2SyntaxAnalyzer:
    """Analyzes Python files for Python 2 specific syntax and patterns."""
    
    # Patterns that indicate Python 2 code
    PY2_PATTERNS = {
        'print_statement': r'^\s*print\s+[^(]',  # print without parentheses (statement)
        'except_comma': r'except\s+\w+\s*,\s*\w+',  # except Exception, e: syntax
        'raise_comma': r'raise\s+\w+\s*,\s*\w+',  # raise Exception, args syntax
        'backtick_repr': r'`[^`]+`',  # `expr` repr syntax
        'long_literal': r'\d+[lL]\b',  # 123L long literal
        'octal_literal': r'\b0[0-7]+\b',  # 0755 octal (not 0o755)
        'unicode_prefix': r"\bu['\"]",  # u'string' unicode prefix
        'xrange_call': r'\bxrange\s*\(',  # xrange() function
        'raw_input_call': r'\braw_input\s*\(',  # raw_input() function
        'has_key_call': r'\.has_key\s*\(',  # dict.has_key() method
        'iteritems_call': r'\.iteritems\s*\(',  # dict.iteritems()
        'iterkeys_call': r'\.iterkeys\s*\(',  # dict.iterkeys()
        'itervalues_call': r'\.itervalues\s*\(',  # dict.itervalues()
        'viewitems_call': r'\.viewitems\s*\(',  # dict.viewitems() (py2.7+)
        'viewkeys_call': r'\.viewkeys\s*\(',  # dict.viewkeys() (py2.7+)
        'viewvalues_call': r'\.viewvalues\s*\(',  # dict.viewvalues() (py2.7+)
        'next_method': r'\.next\s*\(',  # iterator.next() instead of next(iterator)
        'file_xreadlines': r'\.xreadlines\s*\(',  # file.xreadlines()
        'basestring_check': r'\bbasestring\b',  # basestring type
        'cmp_function': r'\bcmp\s*\(',  # cmp() function
        'apply_function': r'\bapply\s*\(',  # apply() function
        'reload_function': r'\breload\s*\(',  # reload() function (now importlib.reload)
        'intern_function': r'\bintern\s*\(',  # intern() function (now sys.intern)
        'unichr_function': r'\bunichr\s*\(',  # unichr() function (now chr())
        'exec_statement': r'^\s*exec\s+\w',  # exec statement (not function)
        'print_chevron': r'>>\s*\w+',  # print >> file syntax
    }
    
    def __init__(self):
        self.files_analyzed = 0
        
    def analyze_file(self, filepath):
        """Analyze a single Python file for Python 2 syntax."""
        findings = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return [{'type': 'error', 'message': f'Could not read file: {e}', 'line': 0}]
        
        # Pattern-based detection
        for pattern_name, pattern in self.PY2_PATTERNS.items():
            try:
                regex = re.compile(pattern, re.MULTILINE)
                for match in regex.finditer(content):
                    line_num = content[:match.start()].count('\n') + 1
                    line_content = lines[line_num - 1] if line_num <= len(lines) else ''
                    findings.append({
                        'type': pattern_name,
                        'line': line_num,
                        'content': line_content.strip()[:100],
                        'description': self._get_description(pattern_name),
                        'severity': self._get_severity(pattern_name)
                    })
            except re.error:
                continue
        
        # AST-based detection for more complex patterns
        try:
            tree = ast.parse(content)
            findings.extend(self._analyze_ast(tree, lines))
        except SyntaxError as e:
            findings.append({
                'type': 'syntax_error_py3',
                'line': e.lineno or 0,
                'content': str(e),
                'description': 'Code contains syntax that Python 3 cannot parse (likely Python 2 only)',
                'severity': 'critical'
            })
        except Exception:
            pass
        
        self.files_analyzed += 1
        return findings
    
    def _analyze_ast(self, tree, lines):
        """Analyze AST for Python 2 patterns."""
        findings = []
        
        for node in ast.walk(tree):
            # Check for Print node (Python 2 print statement)
            if isinstance(node, ast.Print):
                findings.append({
                    'type': 'ast_print_statement',
                    'line': node.lineno,
                    'content': lines[node.lineno - 1].strip()[:100] if node.lineno <= len(lines) else '',
                    'description': 'Python 2 print statement (not function)',
                    'severity': 'critical'
                })
            
            # Check for Exec node (Python 2 exec statement)
            if isinstance(node, ast.Exec):
                findings.append({
                    'type': 'ast_exec_statement',
                    'line': node.lineno,
                    'content': lines[node.lineno - 1].strip()[:100] if node.lineno <= len(lines) else '',
                    'description': 'Python 2 exec statement (not function)',
                    'severity': 'critical'
                })
            
            # Check for old-style Raise with multiple values
            if isinstance(node, ast.Raise):
                if node.inst is not None or node.tback is not None:
                    findings.append({
                        'type': 'ast_raise_old_style',
                        'line': node.lineno,
                        'content': lines[node.lineno - 1].strip()[:100] if node.lineno <= len(lines) else '',
                        'description': 'Python 2 style raise with exception instance',
                        'severity': 'high'
                    })
            
            # Check for old-style class definitions
            if isinstance(node, ast.ClassDef):
                if not node.bases:
                    findings.append({
                        'type': 'ast_old_style_class',
                        'line': node.lineno,
                        'content': lines[node.lineno - 1].strip()[:100] if node.lineno <= len(lines) else '',
                        'description': 'Old-style class definition (no explicit base class)',
                        'severity': 'medium'
                    })
        
        return findings
    
    def _get_description(self, pattern_name):
        """Get human-readable description for a pattern."""
        descriptions = {
            'print_statement': 'Python 2 print statement without parentheses',
            'except_comma': 'Python 2 except clause with comma syntax (use "except Exception as e")',
            'raise_comma': 'Python 2 raise statement with comma syntax',
            'backtick_repr': 'Backtick repr syntax (`expr`) - use repr(expr)',
            'long_literal': 'Long integer literal suffix L (automatic in Python 3)',
            'octal_literal': 'Old-style octal literal (use 0o prefix)',
            'unicode_prefix': "Unicode string prefix u'' (default in Python 3)",
            'xrange_call': 'xrange() function (use range() in Python 3)',
            'raw_input_call': 'raw_input() function (use input() in Python 3)',
            'has_key_call': 'dict.has_key() method (use "key in dict")',
            'iteritems_call': 'dict.iteritems() method (use dict.items())',
            'iterkeys_call': 'dict.iterkeys() method (use dict.keys())',
            'itervalues_call': 'dict.itervalues() method (use dict.values())',
            'viewitems_call': 'dict.viewitems() method (use dict.items())',
            'viewkeys_call': 'dict.viewkeys() method (use dict.keys())',
            'viewvalues_call': 'dict.viewvalues() method (use dict.values())',
            'next_method': 'iterator.next() method (use next(iterator))',
            'file_xreadlines': 'file.xreadlines() method (use file or iter(file))',
            'basestring_check': 'basestring type (use str in Python 3)',
            'cmp_function': 'cmp() function (removed in Python 3)',
            'apply_function': 'apply() function (use direct call with *)',
            'reload_function': 'reload() builtin (use importlib.reload())',
            'intern_function': 'intern() builtin (use sys.intern())',
            'unichr_function': 'unichr() function (use chr() in Python 3)',
            'exec_statement': 'exec statement (use exec() function)',
            'print_chevron': 'Print chevron syntax (print >> file)',
        }
        return descriptions.get(pattern_name, f'Potential Python 2 pattern: {pattern_name}')
    
    def _get_severity(self, pattern_name):
        """Get severity level for a pattern."""
        critical = ['ast_print_statement', 'ast_exec_statement', 'backtick_repr', 
                    'except_comma', 'raise_comma', 'exec_statement', 'syntax_error_py3']
        high = ['xrange_call', 'raw_input_call', 'has_key_call', 'cmp_function',
                'apply_function', 'raise_comma']
        medium = ['old_class_def', 'iteritems_call', 'iterkeys_call', 'itervalues_call',
                  'basestring_check', 'next_method', 'ast_old_style_class', 'ast_raise_old_style']
        low = ['unicode_prefix', 'long_literal', 'octal_literal', 'viewitems_call',
               'viewkeys_call', 'viewvalues_call', 'file_xreadlines']
        
        if pattern_name in critical:
            return 'critical'
        elif pattern_name in high:
            return 'high'
        elif pattern_name in medium:
            return 'medium'
        else:
            return 'low'
    
    def analyze_directory(self, directory, extensions=None):
        """Analyze all Python files in a directory recursively."""
        if extensions is None:
            extensions = ['.py']
        
        all_findings = defaultdict(list)
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                      ['__pycache__', 'node_modules', 'venv', 'env', '.git']]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    findings = self.analyze_file(filepath)
                    if findings:
                        all_findings[filepath] = findings
        
        return dict(all_findings)


def generate_xml_report(findings_by_file, output_path):
    """Generate a detailed XML report of findings."""
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<python2_analysis_report>',
        '  <metadata>',
        '    <analyzer_version>1.0.0</analyzer_version>',
        f'    <python_version>{sys.version}</python_version>',
        f'    <files_analyzed>{len(findings_by_file)}</files_analyzed>',
        '    <description>Detailed analysis of Python 2 syntax and constructs found in the codebase</description>',
        '  </metadata>',
        '  <summary>',
    ]
    
    total_findings = 0
    severity_counts = defaultdict(int)
    type_counts = defaultdict(int)
    
    for filepath, findings in findings_by_file.items():
        for finding in findings:
            total_findings += 1
            severity_counts[finding.get('severity', 'unknown')] += 1
            type_counts[finding.get('type', 'unknown')] += 1
    
    xml_parts.append(f'    <total_findings>{total_findings}</total_findings>')
    xml_parts.append('    <by_severity>')
    for severity, count in sorted(severity_counts.items()):
        xml_parts.append(f'      <{severity}>{count}</{severity}>')
    xml_parts.append('    </by_severity>')
    xml_parts.append('    <by_type>')
    for finding_type, count in sorted(type_counts.items()):
        safe_type = finding_type.replace(" ", "_").replace("-", "_")
        xml_parts.append(f'      <{safe_type}>{count}</{safe_type}>')
    xml_parts.append('    </by_type>')
    xml_parts.append('  </summary>')
    xml_parts.append('  <files>')
    
    for filepath, findings in sorted(findings_by_file.items()):
        xml_parts.append(f'    <file path="{filepath}">')
        xml_parts.append(f'      <finding_count>{len(findings)}</finding_count>')
        xml_parts.append('      <findings>')
        
        for i, finding in enumerate(findings, 1):
            xml_parts.append(f'        <finding id="{i}">')
            xml_parts.append(f'          <type>{finding.get("type", "unknown")}</type>')
            xml_parts.append(f'          <severity>{finding.get("severity", "unknown")}</severity>')
            xml_parts.append(f'          <line>{finding.get("line", 0)}</line>')
            
            content = finding.get('content', '')
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            xml_parts.append(f'          <content><![CDATA[{content}]]></content>')
            
            description = finding.get('description', '')
            description = description.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_parts.append(f'          <description>{description}</description>')
            xml_parts.append('        </finding>')
        
        xml_parts.append('      </findings>')
        xml_parts.append('    </file>')
    
    xml_parts.append('  </files>')
    xml_parts.append('  <reference>')
    xml_parts.append('    <python2_constructs>')
    xml_parts.append('      <construct name="print_statement">')
    xml_parts.append('        <description>In Python 2, print is a statement. In Python 3, it is a function.</description>')
    xml_parts.append('        <example_py2>print "hello"</example_py2>')
    xml_parts.append('        <example_py3>print("hello")</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="except_syntax">')
    xml_parts.append('        <description>Python 2 uses comma to bind exception to variable.</description>')
    xml_parts.append('        <example_py2>except Exception, e:</example_py2>')
    xml_parts.append('        <example_py3>except Exception as e:</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="raise_syntax">')
    xml_parts.append('        <description>Python 2 allows raising with comma-separated values.</description>')
    xml_parts.append('        <example_py2>raise ValueError, "message"</example_py2>')
    xml_parts.append('        <example_py3>raise ValueError("message")</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="backtick_repr">')
    xml_parts.append('        <description>Backticks are shorthand for repr() in Python 2.</description>')
    xml_parts.append('        <example_py2>`x`</example_py2>')
    xml_parts.append('        <example_py3>repr(x)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="long_literals">')
    xml_parts.append('        <description>Python 2 has explicit long integer literals with L suffix.</description>')
    xml_parts.append('        <example_py2>123456789L</example_py2>')
    xml_parts.append('        <example_py3>123456789 (all ints are long in Python 3)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="octal_literals">')
    xml_parts.append('        <description>Python 2 uses 0 prefix for octal, Python 3 requires 0o.</description>')
    xml_parts.append('        <example_py2>0755</example_py2>')
    xml_parts.append('        <example_py3>0o755</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="unicode_strings">')
    xml_parts.append('        <description>Python 2 distinguishes str and unicode. Python 3 str is unicode.</description>')
    xml_parts.append('        <example_py2>u"hello"</example_py2>')
    xml_parts.append('        <example_py3>"hello" (unicode by default)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="xrange">')
    xml_parts.append('        <description>Python 2 has xrange for lazy evaluation, range returns list.</description>')
    xml_parts.append('        <example_py2>xrange(10)</example_py2>')
    xml_parts.append('        <example_py3>range(10) (lazy like xrange)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="raw_input">')
    xml_parts.append('        <description>Python 2 raw_input returns string, input evaluates.</description>')
    xml_parts.append('        <example_py2>raw_input("Enter: ")</example_py2>')
    xml_parts.append('        <example_py3>input("Enter: ")</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="dict_methods">')
    xml_parts.append('        <description>Python 2 has iter* and view* methods for dictionaries.</description>')
    xml_parts.append('        <example_py2>d.iteritems(), d.viewkeys()</example_py2>')
    xml_parts.append('        <example_py3>d.items(), d.keys()</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="has_key">')
    xml_parts.append('        <description>Python 2 dict.has_key() method was removed.</description>')
    xml_parts.append('        <example_py2>d.has_key(k)</example_py2>')
    xml_parts.append('        <example_py3>k in d</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="old_classes">')
    xml_parts.append('        <description>Python 2 has old-style classes without object base.</description>')
    xml_parts.append('        <example_py2>class MyClass:</example_py2>')
    xml_parts.append('        <example_py3>class MyClass(object): (or just class MyClass:)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="basestring">')
    xml_parts.append('        <description>Python 2 basestring is parent of str and unicode.</description>')
    xml_parts.append('        <example_py2>isinstance(x, basestring)</example_py2>')
    xml_parts.append('        <example_py3>isinstance(x, str)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="cmp_function">')
    xml_parts.append('        <description>Python 2 cmp() function compares two values.</description>')
    xml_parts.append('        <example_py2>cmp(a, b)</example_py2>')
    xml_parts.append('        <example_py3>(a > b) - (a < b) or use functools.cmp_to_key</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="apply_function">')
    xml_parts.append('        <description>Python 2 apply() calls function with args tuple.</description>')
    xml_parts.append('        <example_py2>apply(func, args)</example_py2>')
    xml_parts.append('        <example_py3>func(*args)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="intern_function">')
    xml_parts.append('        <description>Python 2 intern() is builtin, Python 3 moved to sys.</description>')
    xml_parts.append('        <example_py2>intern(s)</example_py2>')
    xml_parts.append('        <example_py3>sys.intern(s)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="unichr_function">')
    xml_parts.append('        <description>Python 2 unichr() returns unicode character.</description>')
    xml_parts.append('        <example_py2>unichr(65)</example_py2>')
    xml_parts.append('        <example_py3>chr(65)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="next_method">')
    xml_parts.append('        <description>Python 2 iterators have .next() method.</description>')
    xml_parts.append('        <example_py2>it.next()</example_py2>')
    xml_parts.append('        <example_py3>next(it)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="file_type">')
    xml_parts.append('        <description>Python 2 file type and FileType were removed.</description>')
    xml_parts.append('        <example_py2>isinstance(f, file)</example_py2>')
    xml_parts.append('        <example_py3>isinstance(f, io.IOBase)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="exec_statement">')
    xml_parts.append('        <description>Python 2 exec is a statement, Python 3 it is a function.</description>')
    xml_parts.append('        <example_py2>exec code</example_py2>')
    xml_parts.append('        <example_py3>exec(code)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="print_chevron">')
    xml_parts.append('        <description>Python 2 print supports >> for file output.</description>')
    xml_parts.append('        <example_py2>print >> sys.stderr, "error"</example_py2>')
    xml_parts.append('        <example_py3>print("error", file=sys.stderr)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('      <construct name="division">')
    xml_parts.append('        <description>Python 2 / is integer division for ints, Python 3 is float.</description>')
    xml_parts.append('        <example_py2>5 / 2 == 2 (or use from __future__ import division)</example_py2>')
    xml_parts.append('        <example_py3>5 / 2 == 2.5 (use // for integer division)</example_py3>')
    xml_parts.append('      </construct>')
    xml_parts.append('    </python2_constructs>')
    xml_parts.append('  </reference>')
    xml_parts.append('</python2_analysis_report>')
    
    xml_content = '\n'.join(xml_parts)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    return output_path


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Python 2 Syntax Analyzer')
    parser.add_argument('path', nargs='?', default='/workspace', 
                       help='Path to analyze (file or directory)')
    parser.add_argument('-o', '--output', default='/workspace/python2_analysis.xml',
                       help='Output XML report path')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    analyzer = Python2SyntaxAnalyzer()
    
    if os.path.isfile(args.path):
        findings = {args.path: analyzer.analyze_file(args.path)}
    else:
        findings = analyzer.analyze_directory(args.path)
    
    output_path = generate_xml_report(findings, args.output)
    
    print(f"Analysis complete. Found {sum(len(f) for f in findings.values())} potential Python 2 constructs.")
    print(f"Report saved to: {output_path}")
    
    if args.verbose and findings:
        for filepath, file_findings in findings.items():
            if file_findings:
                print(f"\n{filepath}:")
                for finding in file_findings[:10]:
                    print(f"  Line {finding['line']}: [{finding['severity']}] {finding['type']}")
                if len(file_findings) > 10:
                    print(f"  ... and {len(file_findings) - 10} more")
