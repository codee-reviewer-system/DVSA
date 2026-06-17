"""
Security Vulnerability Test Cases for Semgrep Validation.

This file contains 20+ security vulnerabilities designed to test the worktree
functionality. Key design:

- Many vulnerabilities have their INPUT SOURCE defined 10-40 lines ABOVE
  the vulnerable usage. Without worktrees (diff-only), Semgrep would miss
  these because the input assignment is in "unchanged" code.
- With worktrees, Semgrep sees the FULL file and can trace taint across
  unchanged lines to detect the vulnerability.

Expected Semgrep detection count: 20+ issues
"""

import os
import sqlite3
import subprocess
import hashlib
import pickle
import json
import random
import xml.etree.ElementTree as ET
from urllib import request as url_request

# ============================================================
# VULNERABILITY 1: SQL Injection (taint spans unchanged lines)
# Lines 25-26: input source (would be "unchanged" in PR)
# Line 32: vulnerable query (would be "changed" in PR)
# ============================================================

def get_user_v1(user_id):
    """Input assigned 7 lines above the vulnerable query."""
    query_input = user_id
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    user = cursor.execute(
        f"SELECT * FROM users WHERE id = {query_input}"  # SQL injection
    ).fetchone()
    return user


# ============================================================
# VULNERABILITY 2: SQL Injection via string concatenation
# ============================================================

def get_user_v2(username):
    """Input source 12 lines above vulnerability."""
    search_term = username
    filter_type = "active"
    sort_order = "DESC"

    conn = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE name = '" + search_term + "'"  # SQL injection
    return conn.execute(query).fetchall()


# ============================================================
# VULNERABILITY 3: SQL Injection via f-string in ORM bypass
# ============================================================

def search_products(category, min_price):
    """Taint source is function parameter, flow through local var."""
    cat = category
    price = min_price

    conn = sqlite3.connect("shop.db")
    # User-controlled f-string in raw SQL
    sql = f"SELECT * FROM products WHERE category = '{cat}' AND price > {price}"  # SQL injection
    return conn.execute(sql).fetchall()


# ============================================================
# VULNERABILITY 4: XSS via string concatenation
# Lines 90-91: user input
# Line 98: unsanitized output
# ============================================================

def render_user_profile(user_name):
    """Input assigned 8 lines above the HTML output."""
    name = user_name
    display_name = name.strip()

    return f"<div>Hello, {display_name}</div>"  # XSS - no escaping


# ============================================================
# VULNERABILITY 5: XSS via template literal
# ============================================================

def render_search_results(query, results):
    """Taint flows through variable before reaching output."""
    search_query = query
    html = f"<h1>Results for: {search_query}</h1>"  # XSS
    for r in results:
        html += f"<p>{r}</p>"
    return html


# ============================================================
# VULNERABILITY 6: Command Injection via subprocess
# Lines 115: input source
# Line 124: vulnerable subprocess call
# ============================================================

def ping_host(hostname):
    """Input assigned 9 lines above the subprocess call."""
    host = hostname
    clean_host = host.replace(" ", "")

    result = subprocess.run(  # Command injection
        f"ping -c 1 {clean_host}",
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout


# ============================================================
# VULNERABILITY 7: Command Injection via os.system
# ============================================================

def lookup_dns(domain):
    """Input source far above the os.system call."""
    target = domain
    cmd = "nslookup " + target  # Command injection

    os.system(cmd)
    return "done"


# ============================================================
# VULNERABILITY 8: Path Traversal
# Lines 140: user input
# Line 150: file read without sanitization
# ============================================================

def read_file(filename):
    """Input assigned 10 lines above file operation."""
    file_path = filename
    base_dir = "/var/data"

    full_path = base_dir + "/" + file_path  # Path traversal
    with open(full_path, "r") as f:
        return f.read()


# ============================================================
# VULNERABILITY 9: Path Traversal via os.path.join bypass
# ============================================================

def load_config(config_name):
    """User-controlled path passed to open()."""
    name = config_name
    sanitized = name.replace("..", "")  # Insufficient sanitization

    path = os.path.join("/etc/app", sanitized)  # Still vulnerable
    with open(path, "r") as f:
        return json.load(f)


# ============================================================
# VULNERABILITY 10: Hardcoded API Key
# ============================================================

def init_stripe():
    """Hardcoded secret in function."""
    stripe_key = "sk_live_FAKE_KEY_FOR_TESTING_ONLY_12345"  # Hardcoded secret
    return stripe_key


# ============================================================
# VULNERABILITY 11: Hardcoded Password
# ============================================================

def connect_database():
    """Hardcoded password in connection string."""
    db_password = "SuperSecret123!"  # Hardcoded secret
    conn_str = f"postgresql://admin:{db_password}@localhost/mydb"
    return conn_str


# ============================================================
# VULNERABILITY 12: Hardcoded AWS Key
# ============================================================

def setup_aws():
    """Hardcoded AWS credentials."""
    aws_access = "AKIA_FAKE_KEY_FOR_TESTING_ONLY"  # Hardcoded secret
    aws_secret = "fake_secret_key_for_testing_only_12345"  # Hardcoded secret
    return {"key": aws_access, "secret": aws_secret}


# ============================================================
# VULNERABILITY 13: Hardcoded GitHub Token
# ============================================================

def get_github_token():
    """Hardcoded GitHub personal access token."""
    token = "ghp_FAKE_TOKEN_FOR_TESTING_ONLY_1234567890"  # Hardcoded secret
    return token


# ============================================================
# VULNERABILITY 14: Unsafe Deserialization
# Lines 205: serialized data source
# Line 214: pickle.loads without validation
# ============================================================

def load_user_data(serialized_data):
    """Input assigned 9 lines above the dangerous deserialization."""
    data = serialized_data
    clean_data = data.strip()

    obj = pickle.loads(clean_data)  # Unsafe deserialization
    return obj


# ============================================================
# VULNERABILITY 15: Unsafe eval
# ============================================================

def process_expression(expr):
    """User-controlled input passed to eval()."""
    input_expr = expr
    result = eval(input_expr)  # Unsafe eval
    return result


# ============================================================
# VULNERABILITY 16: Unsafe exec
# ============================================================

def run_user_code(code_snippet):
    """User-controlled code passed to exec()."""
    user_code = code_snippet
    exec(user_code)  # Unsafe exec


# ============================================================
# VULNERABILITY 17: Weak MD5 Hashing
# Lines 235: password source
# Line 245: weak hash algorithm
# ============================================================

def hash_password(password):
    """Input assigned 10 lines above the weak hash."""
    pwd = password
    salt = "staticsalt123"

    hashed = hashlib.md5((pwd + salt).encode()).hexdigest()  # Weak hashing
    return hashed


# ============================================================
# VULNERABILITY 18: Insecure Random for Security
# ============================================================

def generate_session_token():
    """Weak random used for security-critical value."""
    token = random.randint(100000, 999999)  # Insecure random
    return str(token)


# ============================================================
# VULNERABILITY 19: SSRF via user-controlled URL
# Lines 260: URL input
# Line 268: fetch without validation
# ============================================================

def fetch_url(url):
    """Input assigned 8 lines above the URL fetch."""
    target_url = url
    clean_url = target_url.replace(" ", "")

    response = url_request.urlopen(clean_url)  # SSRF
    return response.read()


# ============================================================
# VULNERABILITY 20: XXE via XML parsing
# Lines 275: XML input
# Line 283: XML parse without defusing
# ============================================================

def parse_xml_data(xml_string):
    """Input assigned 8 lines above XML parsing."""
    xml_data = xml_string
    cleaned = xml_data.strip()

    root = ET.fromstring(cleaned)  # XXE vulnerability
    return root.attrib


# ============================================================
# VULNERABILITY 21: LDAP Injection
# ============================================================

def ldap_search(username):
    """User-controlled input in LDAP filter."""
    user = username
    filter_str = f"(uid={user})"  # LDAP injection
    return filter_str


# ============================================================
# VULNERABILITY 22: Log Injection / Information Disclosure
# Lines 300-301: sensitive data
# Line 310: logging secrets
# ============================================================

def login_user(username, password):
    """Input assigned 10 lines above logging."""
    user = username
    pwd = password

    print(f"Login attempt: user={user}, password={pwd}")  # Log injection
    return True


# ============================================================
# VULNERABILITY 23: HTTP Usage (non-TLS)
# ============================================================

def fetch_http_resource():
    """Insecure HTTP usage."""
    url = "http://api.example.com/data"  # HTTP not HTTPS
    response = url_request.urlopen(url)
    return response.read()


# ============================================================
# VULNERABILITY 24: Shell=True with User Input
# ============================================================

def execute_command(user_input):
    """Shell injection via subprocess with shell=True."""
    cmd = f"echo {user_input}"  # Command injection
    result = subprocess.run(cmd, shell=True, capture_output=True)  # shell=True
    return result.stdout


# ============================================================
# VULNERABILITY 25: Insecure Temporary File
# ============================================================

def create_temp_file(data):
    """Predictable temp file name."""
    filename = "/tmp/myapp_" + "userfile"  # Predictable temp path

    with open(filename, "w") as f:
        f.write(data)
    return filename


# ============================================================
# PR 2: NEW VULNERABILITIES BELOW THIS LINE
# These reference variables defined ABOVE (unchanged in PR 2)
# This tests whether worktrees can trace taint across unchanged code
# ============================================================


# ============================================================
# VULNERABILITY 26: SQL Injection via cross-function taint
# 'user_id' parameter comes from get_user_v1 (line 25, unchanged)
# New function uses it in a different query (changed lines)
# ============================================================

def get_user_orders(user_id):
    """References user_id from get_user_v1 context - NEW function."""
    uid = user_id
    conn = sqlite3.connect("orders.db")
    query = "SELECT * FROM orders WHERE user_id = " + uid  # SQL injection
    return conn.execute(query).fetchall()


# ============================================================
# VULNERABILITY 27: Command Injection via cross-function taint
# 'hostname' from ping_host context (line 108, unchanged)
# New function reuses it in a different command (changed lines)
# ============================================================

def check_host_status(hostname):
    """References hostname from ping_host context - NEW function."""
    host = hostname
    output = subprocess.run(
        f"curl -s http://{host}/health",  # Command injection
        shell=True,
        capture_output=True,
        text=True
    )
    return output.stdout


# ============================================================
# VULNERABILITY 28: XSS via cross-function taint
# 'user_name' from render_user_profile context (line 85, unchanged)
# New function uses it unsanitized (changed lines)
# ============================================================

def render_user_card(user_name):
    """References user_name from render_user_profile context - NEW function."""
    name = user_name
    return f"<article class='user-card'><h2>{name}</h2></article>"  # XSS


# ============================================================
# VULNERABILITY 29: Path Traversal via cross-function taint
# 'filename' from read_file context (line 143, unchanged)
# New function reuses it (changed lines)
# ============================================================

def backup_file(filename):
    """References filename from read_file context - NEW function."""
    target = filename
    backup_path = "/tmp/backups/" + target  # Path traversal
    with open(backup_path, "w") as f:
        f.write("backup")
    return backup_path


# ============================================================
# VULNERABILITY 30: Unsafe Deserialization via cross-function taint
# 'data' from load_user_data context (line 208, unchanged)
# New function passes it to pickle (changed lines)
# ============================================================

def clone_user_data(data):
    """References data from load_user_data context - NEW function."""
    raw = data
    copy = pickle.loads(raw)  # Unsafe deserialization
    return copy


# ============================================================
# VULNERABILITY 31: Hardcoded Secret in New Function
# Completely new function with hardcoded credential (changed lines)
# ============================================================

def get_redis_password():
    """New hardcoded secret - all lines changed."""
    redis_pass = "redis_default_pass_2024"  # Hardcoded secret
    return redis_pass


# ============================================================
# VULNERABILITY 32: SSRF via cross-function taint
# 'url' from fetch_url context (line 268, unchanged)
# New function reuses it (changed lines)
# ============================================================

def mirror_url(url):
    """References url from fetch_url context - NEW function."""
    target = url
    import urllib.request
    response = urllib.request.urlopen(target)  # SSRF
    return response.read()
