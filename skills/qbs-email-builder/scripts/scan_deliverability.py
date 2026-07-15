"""
scan_deliverability.py

Run a quick spam-risk analysis on an email before pushing.

Usage:
    from scan_deliverability import scan_email

    result = scan_email(
        subject='Honest take: AI SDRs',
        preview='Real take. Here is what we found.',
        body_html='<p>Hi {{ contact.firstname }},...</p>'
    )
    # result = {'score': 'pass'|'review'|'fail', 'findings': [...], 'recommendations': [...]}

CLI usage:
    python scan_deliverability.py path/to/email.json
"""
import re
import sys
import json


# Spam trigger words. Not exhaustive — but covers the most flagged ones in 2026.
SPAM_TRIGGER_WORDS = [
    'free!!!', 'act now', 'click here now', 'limited time', 'offer expires',
    'no obligation', 'risk free', '100% free', 'amazing offer',
    'congratulations', '$$$', 'winner', 'cash', 'urgent action required',
    'once in a lifetime', 'order now', 'apply now', 'guaranteed',
    'no cost', 'extra income', 'make money', 'best price ever',
    'this is not spam', 'click below', 'while supplies last',
    'no purchase necessary',
]

# Subject line spammy indicators (separate from body)
SUBJECT_SPAMMY_WORDS = [
    'free', 'urgent', 'act now', '$$$', 'winner', 'guaranteed', 'amazing',
    'limited time', 'expires', 'no obligation',
]


def _strip_html(html):
    """Strip HTML tags and collapse whitespace."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def scan_email(subject='', preview='', body_html='', html_size_kb=None):
    """
    Run a deliverability scan on an email.

    Returns a dict with overall 'score' (pass/review/fail), individual 'findings',
    and 'recommendations' for any issues found.
    """
    findings = []
    recommendations = []
    fail_count = 0
    review_count = 0

    text = _strip_html(body_html)
    word_count = len(text.split())

    # 1. HTML size
    if html_size_kb is None:
        html_size_kb = len(body_html.encode('utf-8')) / 1024
    if html_size_kb > 102:
        findings.append({
            'check': 'html_size',
            'status': 'fail',
            'detail': f'HTML size {html_size_kb:.1f} KB exceeds Gmail 102KB clip threshold'
        })
        recommendations.append('Reduce email content or move some sections out')
        fail_count += 1
    elif html_size_kb > 50:
        findings.append({
            'check': 'html_size',
            'status': 'review',
            'detail': f'HTML size {html_size_kb:.1f} KB is approaching Gmail clip threshold'
        })
        review_count += 1
    else:
        findings.append({
            'check': 'html_size',
            'status': 'pass',
            'detail': f'{html_size_kb:.1f} KB (well under 102KB threshold)'
        })

    # 2. Image-to-text ratio
    img_count = len(re.findall(r'<img', body_html, re.IGNORECASE))
    if word_count > 0:
        ratio = img_count / word_count * 100
        if img_count > 5 and word_count < 100:
            findings.append({
                'check': 'image_text_ratio',
                'status': 'fail',
                'detail': f'{img_count} images for only {word_count} words — heavy image-to-text ratio'
            })
            recommendations.append('Add more text content or reduce images')
            fail_count += 1
        elif word_count >= 100:
            findings.append({
                'check': 'image_text_ratio',
                'status': 'pass',
                'detail': f'{img_count} images, {word_count} words (healthy ratio)'
            })

    # 3. Spam trigger words in body
    text_lower = text.lower()
    body_triggers = [w for w in SPAM_TRIGGER_WORDS if w in text_lower]
    if body_triggers:
        findings.append({
            'check': 'body_spam_words',
            'status': 'fail',
            'detail': f'Found spam trigger words: {body_triggers}'
        })
        recommendations.append(f'Rewrite to remove: {", ".join(body_triggers)}')
        fail_count += 1
    else:
        findings.append({
            'check': 'body_spam_words',
            'status': 'pass',
            'detail': 'No spam trigger words in body'
        })

    # 4. Subject line analysis
    subject_lower = subject.lower()
    subject_caps_words = re.findall(r'\b[A-Z]{4,}\b', subject)
    subject_excl = subject.count('!')
    subject_spammy = [w for w in SUBJECT_SPAMMY_WORDS if w in subject_lower]

    subject_issues = []
    if len(subject_caps_words) > 1:
        subject_issues.append(f'{len(subject_caps_words)} ALL-CAPS words')
    if subject_excl > 1:
        subject_issues.append(f'{subject_excl} exclamation marks')
    if subject_spammy:
        subject_issues.append(f'spammy words: {subject_spammy}')

    if subject_issues:
        findings.append({
            'check': 'subject_line',
            'status': 'fail' if subject_spammy else 'review',
            'detail': '; '.join(subject_issues)
        })
        recommendations.append('Rewrite subject — too many spam signals')
        if subject_spammy:
            fail_count += 1
        else:
            review_count += 1
    else:
        findings.append({
            'check': 'subject_line',
            'status': 'pass',
            'detail': f'"{subject}" — clean'
        })

    # 5. Hidden content check
    hidden_patterns = [
        (r'color:\s*#fff[fe]?[fe]?[fe]?[^a-z]', 'White text'),
        (r'font-size:\s*[012]px', 'Tiny font (<3px)'),
        (r'display:\s*none', 'display:none'),
        (r'visibility:\s*hidden', 'visibility:hidden'),
    ]
    hidden_issues = []
    for pat, desc in hidden_patterns:
        matches = re.findall(pat, body_html, re.IGNORECASE)
        if matches:
            # Filter out CTA buttons (white-on-color is normal)
            if desc == 'White text' and 'background-color' in body_html and 'background_color' not in pat:
                continue
            # Filter out spacer divs (3px on background fills is normal)
            if desc == 'Tiny font (<3px)' and 'height:3px' in body_html:
                continue
            hidden_issues.append(f'{desc}: {len(matches)}')

    if hidden_issues:
        findings.append({
            'check': 'hidden_content',
            'status': 'review',
            'detail': '; '.join(hidden_issues)
        })
        review_count += 1
    else:
        findings.append({
            'check': 'hidden_content',
            'status': 'pass',
            'detail': 'No hidden content tricks'
        })

    # 6. Excessive caps/punctuation in body
    caps_in_body = len(re.findall(r'\b[A-Z]{4,}\b', text))
    excl_in_body = text.count('!')
    if caps_in_body > 5 or excl_in_body > 5:
        findings.append({
            'check': 'body_formatting',
            'status': 'review',
            'detail': f'{caps_in_body} ALL-CAPS words, {excl_in_body} exclamation marks'
        })
        recommendations.append('Tone down the formatting — too aggressive')
        review_count += 1
    else:
        findings.append({
            'check': 'body_formatting',
            'status': 'pass',
            'detail': 'Conversational tone'
        })

    # 7. Link analysis
    links = re.findall(r'href=["\']([^"\']+)["\']', body_html)
    if len(links) > 15:
        findings.append({
            'check': 'link_count',
            'status': 'review',
            'detail': f'{len(links)} links — high count may trigger filters'
        })
        recommendations.append('Consider reducing the number of links')
        review_count += 1
    else:
        findings.append({
            'check': 'link_count',
            'status': 'pass',
            'detail': f'{len(links)} links (acceptable)'
        })

    # Overall score
    if fail_count > 0:
        score = 'fail'
    elif review_count > 0:
        score = 'review'
    else:
        score = 'pass'

    return {
        'score': score,
        'fail_count': fail_count,
        'review_count': review_count,
        'pass_count': len(findings) - fail_count - review_count,
        'findings': findings,
        'recommendations': recommendations,
        'word_count': word_count,
        'html_size_kb': round(html_size_kb, 2),
    }


def print_report(scan_result):
    """Print a human-readable report from a scan_email result."""
    print(f"=== DELIVERABILITY SCAN ===")
    print(f"Score: {scan_result['score'].upper()}")
    print(f"  Pass: {scan_result['pass_count']}, Review: {scan_result['review_count']}, Fail: {scan_result['fail_count']}")
    print()
    for f in scan_result['findings']:
        icon = {'pass': '✓', 'review': '⚠', 'fail': '✗'}[f['status']]
        print(f"  {icon} {f['check']}: {f['detail']}")
    if scan_result['recommendations']:
        print()
        print("Recommendations:")
        for r in scan_result['recommendations']:
            print(f"  - {r}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scan_deliverability.py <email.json>")
        print("       (or call scan_email() programmatically)")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        email_data = json.load(f)
    result = scan_email(
        subject=email_data.get('subject', ''),
        preview=email_data.get('preview', ''),
        body_html=email_data.get('body_html', '') or email_data.get('html', ''),
    )
    print_report(result)
