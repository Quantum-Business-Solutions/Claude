import re
orig=open('template_orig.html').read()
t=orig

# 1. remove the three-colour bar row
bar=re.search(r"<tr><td style='padding:0; font-size:0; line-height:0;'>\s*<table[^>]*>\s*<tr>\s*<td bgcolor='#94C83D' width='46%'.*?</table>\s*</td></tr>\s*",t,re.S)
assert bar, 'bar'
t=t.replace(bar.group(0),'')

# 2. css additions (inside the existing <style> block, before </style>)
CSS="""
/* Nasim feedback 23 Nov 2026: banner and bands run edge to edge, PS is a separate rounded box, borders stay rounded */
.hse-section { padding-left: 0 !important; padding-right: 0 !important; }
.hse-section-first { padding-top: 0 !important; }
.hse-section-last { padding-left: 24px !important; padding-right: 24px !important; padding-top: 0 !important; padding-bottom: 34px !important; }
.hse-section-last .hse-column-container { border-collapse: separate !important; border-radius: 16px !important; overflow: hidden !important; }
.hse-section-last .hs_padded { padding-left: 16px !important; padding-right: 16px !important; }
.chip-a { display: inline-block; text-decoration: none; }
"""
assert t.count('</style>')==1
t=t.replace('</style>',CSS+'</style>')
# mobile: keep the PS box gutters tidy
t=t.replace('@media only screen and (max-width: 400px) {','@media only screen and (max-width: 400px) { .hse-section-last { padding-left: 14px !important; padding-right: 14px !important; }',1)

# 3. chips: pill border on the link itself, not on a table cell (table cells lose their rounded border in HubSpot's collapsed-table reset)
chip=re.compile(r"<td class='chip-td' style='padding:0 5px 8px 5px;'><table role='presentation' cellpadding='0' cellspacing='0' border='0'><tr><td class='chip-out chip-bg' bgcolor='#ffffff' style='background-color:#ffffff; border:1px solid #DCE7F0; border-radius:100px; padding:13px 16px;'><a href='([^']+)' class='t-blue' style='font-family:Poppins, Helvetica, Arial, sans-serif; font-size:13px; font-weight:600; color:#004B87; text-decoration:none;'>(.*?)</a></td></tr></table></td>",re.S)
def rep(m):
    return ("<td class='chip-td' style='padding:0 5px 8px 5px;'><a href='%s' class='chip-a chip-out chip-bg t-blue' style='display:inline-block; background-color:#ffffff; border:1px solid #DCE7F0; border-radius:100px; padding:13px 16px; line-height:1.2; font-family:Poppins, Helvetica, Arial, sans-serif; font-size:13px; font-weight:600; color:#004B87; text-decoration:none;'>%s</a></td>"%(m.group(1),m.group(2)))
t,nchip=chip.subn(rep,t); assert nchip==5,nchip

# 4. call button: outline on the link itself
call=re.compile(r"<table role='presentation' cellpadding='0' cellspacing='0' border='0' style='margin:0 auto;'><tr><td align='center' style='border:1.5px solid #94C83D; border-radius:100px; padding:14px 28px;'><a href='tel:\+18188741200' style='[^']*'>Call \(818\) 874-1200</a></td></tr></table>")
newcall="<a href='tel:+18188741200' style='display:inline-block; border:1.5px solid #94C83D; border-radius:100px; padding:14px 28px; line-height:1.2; font-family:Poppins, Helvetica, Arial, sans-serif; font-size:14px; font-weight:600; color:#94C83D; text-decoration:none;'>Call (818) 874-1200</a>"
t,nc=call.subn(newcall,t); assert nc==1,nc

# 5. outer card: separate-border model so the 20px corners and the clip survive the collapsed-table reset
oc="style='max-width:600px; width:100%; background-color:#ffffff; border-radius:20px; overflow:hidden;"
assert t.count(oc)==1
t=t.replace(oc,"style='max-width:600px; width:100%; border-collapse:separate; border-spacing:0; background-color:#ffffff; border-radius:20px; overflow:hidden;")

# 6. last dnd section (P.S.) sits on white so the pale box is a separate rounded box
ps=re.compile(r"\{% dnd_section background_color='#F2F7FB' %\}(\s*\{% dnd_column %\}\{% dnd_row %\}\s*\{% dnd_module path='@hubspot/rich_text' %\}\s*\{% module_attribute 'html' %\}<p style='margin:0; font-family:Poppins, Helvetica, Arial, sans-serif; font-size:14px; line-height:1.65; color:#44576B;'><strong style='color:#004B87;'>P.S.)")
# keep the section background as the pale box colour (the column container is the rounded box); the gutters come from .hse-section-last padding
open('template_new.html','w').write(t)
print('new template',len(t),'orig',len(orig))
