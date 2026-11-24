import re,json,html as H
HS_HEAD="""<style>
table{border-spacing:0;border-collapse:collapse;mso-table-lspace:0pt;mso-table-rspace:0pt}
td{border-collapse:collapse;mso-line-height-rule:exactly;font-family:Arial,sans-serif;font-size:15px;color:#23496d;word-break:break-word}
.hse-body-wrapper-table{width:100%}
.hse-column-container{min-width:280px;max-width:600px;width:100%;margin-left:auto;margin-right:auto;border-collapse:collapse;border-spacing:0;display:table}
.hse-column{display:table-cell;vertical-align:top}
.hse-size-12{max-width:600px;width:600px}
@media(max-width:639px){.hse-column-container{display:block}.hse-column{display:block;width:100%!important;max-width:100%!important}.hs_padded{padding-left:20px!important;padding-right:20px!important}}
</style>"""
def sections_from_template(t):
    secs=re.findall(r"\{% dnd_section background_color='(#[0-9A-Fa-f]{6})' %\}(.*?)\{% end_dnd_section %\}",t,re.S)
    out=[]
    for bg,body in secs:
        kind='button' if '@hubspot/button_email' in body else 'rich'
        out.append((bg,kind))
    return out
def css_of(d):
    return ';'.join('%s:%s'%(k,v) for k,v in d.items())
def render(tpl,email,hs=True):
    w=email['content']['widgets']
    secs=sections_from_template(tpl)
    n=len(secs)
    parts=[]
    for i,(bg,kind) in enumerate(secs):
        m=w.get('module-%d-0-0'%i)
        b=m['body']
        wcss=css_of(b.get('hs_wrapper_css',{}))
        if kind=='rich':
            inner="<div class='hs_cos_wrapper_type_rich_text'>%s</div>"%b['html']
        else:
            st=b['style']; fs=st['font_style']
            inner=("<div style='text-align:%s'><a href='%s' style='display:inline-block; background-color:%s; color:%s; border-radius:%spx; padding:%spx %spx; font-family:%s; font-size:%spx; font-weight:bold; text-decoration:none;'>%s</a></div>"
              %(st['alignment'],b['destination'],st['background_color']['color'],fs['color'],st['corner_radius'],st['inner_vertical_padding'],st['inner_horizontal_padding'],fs['font'],fs['size']['value'],H.escape(b['text'])))
        cls='hse-section'+(' hse-section-first' if i==0 else '')+(' hse-section-last' if i==n-1 else '')
        ssty='padding-left:10px; padding-right:10px;'+(' padding-top:20px;' if i==0 else '')+(' padding-bottom:20px;' if i==n-1 else '')
        parts.append("<div class='%s' style='%s'><div class='hse-column-container' style='min-width:280px; max-width:600px; width:100%%; margin-left:auto; margin-right:auto; border-collapse:collapse; border-spacing:0; background-color:%s;'><div class='hse-column hse-size-12'><table role='presentation' cellpadding='0' cellspacing='0' width='100%%'><tbody><tr><td class='hs_padded' style='%s'>%s</td></tr></tbody></table></div></div></div>"%(cls,ssty,bg,wcss,inner))
    area=''.join(parts)
    t=re.sub(r"\{% dnd_area 'main'.*?\{% end_dnd_area %\}",lambda m:area,tpl,flags=re.S)
    t=t.replace('{{ standard_header_includes }}',HS_HEAD if hs else '').replace('{{ dnd_area_stylesheet }}','').replace('{{ standard_footer_includes }}','')
    t=t.replace('{{ content.subject }}',H.escape(email['subject']))
    pv=w['preview_text']['body']['value']
    t=re.sub(r"\{% text 'preview_text'.*?%\}",H.escape(pv),t,flags=re.S)
    t=t.replace('{{ site_settings.company_name }}','GoodSuite').replace('{{ site_settings.company_street_address_1 }}','5950 Canoga Ave').replace('{{ site_settings.company_city }}','Woodland Hills').replace('{{ site_settings.company_state }}','CA').replace('{{ site_settings.company_zip }}','91367')
    t=re.sub(r"\{% if site_settings.company_street_address_2 %\}.*?\{% endif %\}",'',t)
    t=t.replace('{{ unsubscribe_link }}','#').replace('{{ unsubscribe_link_all }}','#')
    t=re.sub(r"\{\{ personalization_token\('[^']*', '([^']*)'\) \}\}",r'\1',t)
    t=re.sub(r"<!--.*?-->",'',t,flags=re.S) if False else t
    t=t.replace('<body','<body',1)
    return t
