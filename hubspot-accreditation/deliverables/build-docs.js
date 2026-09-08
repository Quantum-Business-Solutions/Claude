const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,HeadingLevel,AlignmentType,Table,TableRow,TableCell,WidthType,ShadingType,BorderStyle,PageOrientation,ImageRun,Footer,PageNumber,LevelFormat,convertInchesToTwip}=require('docx');

const NAVY="0A1F44",GOLD="C9A227",GREY="5A6470",LIGHT="F4F5F7",BORDER="D8DDE3",INK="1A1A1A",RED="8B1E1E",GREEN="2F6B4F";
const CW=[3000,7440]; const TW=10440;

const noBorder={top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE}};
const cellB={top:{style:BorderStyle.SINGLE,size:4,color:BORDER},bottom:{style:BorderStyle.SINGLE,size:4,color:BORDER},left:{style:BorderStyle.SINGLE,size:4,color:BORDER},right:{style:BorderStyle.SINGLE,size:4,color:BORDER}};

const P=(t,o={})=>new Paragraph({spacing:{after:o.after??140,line:280},alignment:o.align,children:[new TextRun({text:t,size:o.size??21,color:o.color??INK,bold:o.bold,italics:o.italics,font:"Calibri"})]});
const Rich=(runs,o={})=>new Paragraph({spacing:{after:o.after??140,line:280},children:runs.map(r=>new TextRun({text:r.t,size:r.size??21,color:r.color??INK,bold:r.bold,italics:r.italics,font:"Calibri"}))});
const H1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,spacing:{before:340,after:160},children:[new TextRun({text:t,size:28,bold:true,color:NAVY,font:"Calibri"})]});
const H2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,spacing:{before:260,after:120},children:[new TextRun({text:t,size:23,bold:true,color:"2E4057",font:"Calibri"})]});
const Bullet=t=>new Paragraph({numbering:{reference:"bul",level:0},spacing:{after:80,line:280},children:[new TextRun({text:t,size:21,color:INK,font:"Calibri"})]});
const Rule=()=>new Paragraph({spacing:{after:180},border:{bottom:{style:BorderStyle.SINGLE,size:8,color:GOLD}},children:[new TextRun({text:"",size:2})]});

function cell(text,{bold,fill,w,color,size}={}){return new TableCell({width:{size:w,type:WidthType.DXA},shading:fill?{type:ShadingType.CLEAR,fill}:undefined,margins:{top:90,bottom:90,left:130,right:130},borders:cellB,children:[new Paragraph({spacing:{after:0,line:260},children:[new TextRun({text:text,size:size??20,bold,color:color??INK,font:"Calibri"})]})]});}

function kvTable(rows){return new Table({columnWidths:CW,width:{size:TW,type:WidthType.DXA},rows:rows.map(([k,v])=>new TableRow({children:[cell(k,{bold:true,fill:LIGHT,w:CW[0]}),cell(v,{w:CW[1]})]}))});}

function gridTable(header,rows,widths){return new Table({columnWidths:widths,width:{size:TW,type:WidthType.DXA},rows:[
 new TableRow({tableHeader:true,children:header.map((h,i)=>cell(h,{bold:true,fill:NAVY,color:"FFFFFF",w:widths[i]}))}),
 ...rows.map(r=>new TableRow({children:r.map((c,i)=>cell(c,{w:widths[i]}))}))]});}

function callout(title,lines,tone){const fill=tone==="gap"?"FDF6E3":tone==="risk"?"FBEEEE":"EDF5F0";const bar=tone==="gap"?GOLD:tone==="risk"?RED:GREEN;
 return new Table({columnWidths:[TW],width:{size:TW,type:WidthType.DXA},rows:[new TableRow({children:[new TableCell({width:{size:TW,type:WidthType.DXA},shading:{type:ShadingType.CLEAR,fill},margins:{top:150,bottom:150,left:180,right:180},
 borders:{top:{style:BorderStyle.SINGLE,size:4,color:bar},bottom:{style:BorderStyle.SINGLE,size:4,color:bar},left:{style:BorderStyle.SINGLE,size:24,color:bar},right:{style:BorderStyle.SINGLE,size:4,color:bar}},
 children:[new Paragraph({spacing:{after:70},children:[new TextRun({text:title,bold:true,size:20,color:bar,font:"Calibri"})]}),...lines.map(l=>new Paragraph({spacing:{after:50,line:260},children:[new TextRun({text:l,size:20,color:INK,font:"Calibri"})]}))]})]})]});}

function banner(title,sub,tag){return [
 new Table({columnWidths:[TW],width:{size:TW,type:WidthType.DXA},rows:[new TableRow({children:[new TableCell({width:{size:TW,type:WidthType.DXA},shading:{type:ShadingType.CLEAR,fill:NAVY},margins:{top:260,bottom:260,left:220,right:220},borders:noBorder,children:[
  new Paragraph({spacing:{after:90},children:[new TextRun({text:tag,size:18,bold:true,color:GOLD,font:"Calibri",characterSpacing:40})]}),
  new Paragraph({spacing:{after:80},children:[new TextRun({text:title,size:34,bold:true,color:"FFFFFF",font:"Calibri"})]}),
  new Paragraph({spacing:{after:0},children:[new TextRun({text:sub,size:21,color:"D8DDE3",font:"Calibri"})]})]})]})]}),
 new Paragraph({spacing:{after:200},children:[]})];}

const numbering={config:[{reference:"bul",levels:[{level:0,format:LevelFormat.BULLET,text:"•",alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:convertInchesToTwip(0.3),hanging:convertInchesToTwip(0.18)}}}}]}]};

function makeDoc(children){return new Document({numbering,styles:{default:{document:{run:{font:"Calibri",size:21,color:INK}}}},sections:[{properties:{page:{size:{width:12240,height:15840},margin:{top:1080,bottom:1080,left:900,right:900}}},
 footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({text:"Quantum Business Solutions  |  HubSpot Solutions Partner Accreditation  |  Page ",size:16,color:GREY,font:"Calibri"}),new TextRun({children:[PageNumber.CURRENT],size:16,color:GREY,font:"Calibri"})]})]})},
 children}]});}

const img=fs.readFileSync("assets/pactec-dataflow.png");
const imgCF=fs.readFileSync("assets/calcfocus-journey.png");

/* ============ ITEM 1 — CalcFocus OBO Project Plan ============ */
const item1=[...banner("Objectives-Based Onboarding Project Plan","CalcFocus  |  Marketing Hub Professional + Sales Hub Professional  |  April – July 2026","ONBOARDING ACCREDITATION — SUBMISSION ITEM 1"),
H1("Engagement Overview"),
kvTable([["Customer","CalcFocus (calcfocus.com)"],["HubSpot Portal ID","[TO BE INSERTED — customer portal ID]"],["Industry","Computer Software"],["Company size","58 employees"],["Location","Philadelphia, Pennsylvania, USA"],["Engagement start","22 April 2026 (portal opened) / 27 April 2026 (plan of record)"],["Onboarding completion","17 July 2026 — client confirmed"],["Hubs onboarded","Marketing Hub, Sales Hub"],["Subscription levels","Marketing Hub Professional, Sales Hub Professional"],["Users onboarded","[TO BE INSERTED] — 10 attended the 17 July training"],["Delivery partner","Quantum Business Solutions"]]),
new Paragraph({spacing:{after:200},children:[]}),
callout("Value realised inside 90 days",["Kickoff 27 April 2026. Full team training delivered on live, migrated data on 16–17 July 2026 — day 80–81 of the engagement.","All 75 onboarding tasks were complete and client-confirmed within the 90-day window."],"ok"),
new Paragraph({spacing:{after:220},children:[]}),

H1("1. Objectives and Scope"),
P("CalcFocus, a 58-person software business, had purchased HubSpot but had not implemented it. There was no trustworthy CRM baseline. Contact data sat in spreadsheets and disconnected lists. Pipeline data sat with individual sellers. Sales stage nomenclature did not match how the business actually forecast. There was no lifecycle model, no segmentation, no marketing infrastructure and no reporting layer."),
H2("In scope"),
Bullet("Two-hub implementation across Marketing Hub and Sales Hub"),
Bullet("Migration of contact, deal, account and product data into HubSpot"),
Bullet("Lifecycle stage and segmentation architecture"),
Bullet("Lead routing, attribution and reporting"),
Bullet("End-user enablement and administrator handover"),
H2("Out of scope"),
P("Scope discipline was built into the plan rather than managed informally. The project plan carries a dedicated “Wish List — Items Identified Out of Scope During Onboarding” phase. Requests surfacing mid-engagement were captured there and deferred to the post-onboarding roadmap, so neither silently absorbed nor lost."),

H1("2. Key Roles and Responsibilities"),
gridTable(["Organisation","Stakeholders","Responsibility"],[
["Quantum Business Solutions","Shawn Peterson, Marko Ajder, Patrick Dodge, Barb Peterson, Jelena Andric","Onboarding delivery, configuration, migration, enablement"],
["CalcFocus — executive","Lucy, Steve Meade","Sponsorship, forecast model definition, sign-off"],
["CalcFocus — sales","Nate, Alex Terruso","Pipeline data, deal stage validation, sales process input"],
["CalcFocus — marketing / ops","Christine Peart, Kristin Wheeler, Pam Doggett, Lori Baca, MacKenzie Braun","Product library, list data, campaign requirements, end users"]],[2200,3600,4640]),
new Paragraph({spacing:{after:180},children:[]}),
P("Responsibilities were assigned at task level rather than by role description. A distinct set of plan tasks is flagged as client actions and was gated before kickoff rather than chased afterwards: brand assets, Microsoft 365 admin consent, DNS provider access, WordPress admin access, internal IP addresses for tracking exclusion, the existing contacts spreadsheet, ad and social account connections, and three configuration questionnaires."),

H1("3. Onboarding Journey and Timeline"),
P("The engagement ran as an eight-phase gated plan. All 75 onboarding tasks were completed."),
gridTable(["Phase","Tasks","Complete","Outcome"],[
["Pre-Kickoff","7","7 (100%)","Client prerequisites gated before kickoff"],
["HubSpot Kick-Off","9","9 (100%)","Goals, KPIs, stakeholders, SoW and Mutual Commitment reviewed"],
["Foundational Configuration","21","21 (100%)","Lifecycle, personas, routing, segmentation, integrations"],
["Marketing Hub Configuration","25","25 (100%)","Sending domain, forms, nurture framework, dashboard"],
["Sales Hub Set-Up","12","12 (100%)","Pipeline, dashboard, task queues, custom outcomes"],
["Onboarding Wrap-Up","1","1 (100%)","Client confirmation of completion"],
["TOTAL ONBOARDING","75","75 (100%)",""]],[3200,1100,1500,4640]),
new Paragraph({spacing:{after:180},children:[]}),
P("Two further phases sit outside the onboarding scope: an ongoing client-success phase (45 of 76 tasks closed to date) and the out-of-scope wish list."),
new Paragraph({spacing:{after:100},alignment:AlignmentType.CENTER,children:[new ImageRun({type:"png",data:imgCF,transformation:{width:660,height:290}})]}),
P("Figure 1 — The CalcFocus onboarding journey, its parallel migration workstream, the communication and feedback cadence, and the three hand-off gates.",{size:18,color:GREY,italics:true,align:AlignmentType.CENTER}),

H1("4. Communication Plan"),
gridTable(["Channel","Cadence","Purpose"],[
["Client success meeting","Weekly","Progress, blockers, decisions"],
["Strategic review","Monthly — booked through December 2026","Roadmap and value review"],
["Working sessions","On demand","Hands-on configuration with the client team"],
["Recap emails","After each key session","Action items, owners, next steps"],
["Session recordings","Every recorded session","Supplied to the client for their own archives"]],[2800,3200,4440]),
new Paragraph({spacing:{after:180},children:[]}),
P("All correspondence is logged against the CRM record: 19 calls, approximately 230 emails, 36 meetings and 30 transcripts."),

H1("5. Success Metrics and Hand-off Criteria"),
H2("Hand-off criteria"),
P("Three formal client confirmation gates were built into the plan and all three are closed:"),
Bullet("Client Confirmation of Marketing Hub Configuration"),
Bullet("Client Confirmation of Sales Hub Configuration"),
Bullet("Client Confirmation of HubSpot Onboarding Completion"),
P("Hand-off from onboarding to ongoing account management is evidenced by the transition to the retained client-success cadence, with weekly meetings and monthly strategic reviews scheduled through December 2026."),
H2("Success metrics"),
callout("TO COMPLETE BEFORE SUBMISSION",["This section must state the KPIs agreed at kickoff that defined success for CalcFocus.","Submission item 3 then requires actual numbers reported against these same KPIs, so the two documents must use an identical metric set.","Source: the kickoff record, or confirm directly with Lucy and Christine Peart at the next monthly strategic review.","Suggested metrics: pipeline visibility, forecast accuracy, records migrated by object, lead response time, marketing-sourced pipeline, weekly active users."],"gap"),

H1("6. Risk Management"),
gridTable(["Risk identified","Mitigation delivered"],[
["Client-side dependencies stalling the build","Gated as explicit pre-kickoff tasks with named owners, completed before kickoff"],
["Migrating unreliable or duplicated data","Joint client/QBS verification of imported baseline data; deal data routed to the sales owner for review before final import"],
["Training landing on sample rather than real data","Training deliberately scheduled after migration completed, so the team trained on their own live records"],
["Scope creep during onboarding","Standing out-of-scope wish list maintained throughout the engagement"],
["Configured pipeline not matching the business forecast model","Sales stage nomenclature and probability percentages rebuilt to the client's own model as specified by the sales leadership"],
["Capability gaps at the licensed tier","Enterprise-only churn reporting identified early; workarounds built using calculated properties rather than pushing a licence upgrade"]],[3800,6640]),

H1("7. Training Strategy"),
P("Training was sequenced deliberately after data migration so that every session ran against the client's own live records."),
gridTable(["Session","Date","Audience"],[
["HubSpot Working Session","16 July 2026","Core project team"],
["HubSpot Training Session","17 July 2026","Full team — 10 attendees, recorded with transcript"],
["HubSpot Sales Training Session","17 July 2026","Sales and marketing teams"],
["Email and marketing setup session","Scheduled on demand","Marketing owners"]],[4200,2400,3840]),
new Paragraph({spacing:{after:180},children:[]}),
P("Enablement was also embedded throughout the plan rather than confined to set-piece sessions. Over twenty discrete education tasks cover workflow creation, lead statuses, record creation forms, uploading records, brand guidelines, campaigns, nurture content, lead scoring, blog settings, CTAs, forms, chatbot, custom ad audiences, source data, Google Analytics integration, sales sequences, meeting links, meeting and call outcomes, and sales collateral. Named client staff were enrolled in Quantum Academy."),
callout("TO COMPLETE BEFORE SUBMISSION",["HubSpot asks this section to name the documentation delivered — administrator guides, integration documentation, troubleshooting FAQs.","Recorded sessions and Quantum Academy enrolment are evidenced. Confirm which written artefacts exist and attach them.","Known candidate: the CalcFocus Outlook integration overview document."],"gap"),

H1("8. Feedback Mechanisms"),
Bullet("Weekly client success meeting as the standing feedback loop throughout the engagement"),
Bullet("Three client questionnaires — Email Type, Email Settings, Forms Settings — feeding configuration decisions directly"),
Bullet("Client review gate on migrated deal data before final import"),
Bullet("A standing plan task to provide ongoing support for dashboard and report adjustments as feedback is received, making feedback-driven iteration a planned activity rather than an incidental one"),
Bullet("Three formal client confirmation gates at hub and engagement level"),
];

/* ============ ITEM 3 — CalcFocus Project Review ============ */
const item3=[...banner("Project Review","CalcFocus  |  Marketing Hub Professional + Sales Hub Professional  |  April – July 2026","ONBOARDING ACCREDITATION — SUBMISSION ITEM 3"),
Rich([{t:"Companion document. ",bold:true},{t:"This review covers the same engagement profiled in submission item 1, the CalcFocus Objectives-Based Onboarding Project Plan, as the accreditation reuse rule requires."}]),
Rule(),
H1("1. Executive Summary"),
P("CalcFocus moved from an unimplemented HubSpot instance to a live, two-hub revenue system inside 90 days of kickoff."),
P("At the point of engagement the business had bought HubSpot and done nothing with it. Contact data was scattered across spreadsheets, pipeline lived with individual sellers, and the deal stages available in the tool did not describe how the company actually forecast revenue. Quantum Business Solutions delivered a gated, objectives-based onboarding across Marketing Hub and Sales Hub, migrated four distinct data sets into the platform, built the lifecycle, segmentation, routing and reporting layers, and trained the team on their own live records."),
P("All 75 onboarding tasks were completed. The client confirmed completion at three separate formal gates — Marketing Hub, Sales Hub, and the onboarding overall. The engagement converted from a project into a retained relationship, with weekly client success meetings and monthly strategic reviews booked through December 2026."),
P("The defining characteristic of this engagement was adapting the platform to the business rather than the reverse: rebuilding the forecast model to the client's own nomenclature, and engineering around a licence-tier limitation instead of selling an upgrade."),

H1("2. Key Achievements and Deliverables"),
H2("Delivered"),
gridTable(["Area","Delivered"],[
["Onboarding completion","75 of 75 tasks complete; three client confirmation gates closed"],
["Segmentation","Q2 Universal List Library — 111 new lists"],
["Lifecycle and personas","Q2 lifecycle stage workflows; persona properties and buyer persona workflow; “Former Customer” lifecycle workflow remediated"],
["Routing","Round-robin lead assignment workflow"],
["Attribution","Q2 Attribution and Sequence Package deployed via Supered"],
["Marketing Hub","Email sending domain with DKIM/SPF/DMARC; four form templates; nurture campaign framework; marketing dashboard; WordPress tracking code"],
["Sales Hub","Sales dashboard; deals pipeline and active lists; task queues; custom call outcomes, meeting types and meeting outcomes"],
["Data migration","Contacts; pipeline and deals with company associations and stages; carrier accounts with custom properties; product library; event-origin sourcing property; portal-wide domain backfill"],
["Integrations","LinkedIn Sales Navigator; Microsoft 365 mail and calendar"],
["Enablement","Three training sessions on live data; Quantum Academy enrolment; 20+ embedded education tasks"]],[2400,8040]),
new Paragraph({spacing:{after:200},children:[]}),
callout("TO COMPLETE BEFORE SUBMISSION — REQUIRED",["HubSpot requires this section to report ACTUAL NUMBERS against the success metrics defined in submission item 1.","Deliverable counts alone will not satisfy the requirement. The two documents must use the same metric set.","Until real before-and-after figures are inserted here, this item is not ready to submit.","Capture at the next monthly strategic review with Lucy and Christine Peart."],"risk"),

H1("3. Challenges, Issues and Lessons Learned"),
H2("No trustworthy data baseline"),
P("Contact data was spread across spreadsheets and individual sellers, with no single reliable source. Rather than import and correct afterwards, a joint client/QBS verification step was gated into the plan, and migrated deal data was routed to the sales owner for review before final import. Lesson: a review gate before final import costs a week and saves a quarter of remediation."),
H2("The forecast model did not match the tool"),
P("Out-of-the-box deal stages did not reflect how CalcFocus forecast revenue. Stage nomenclature and probability percentages were rebuilt to the client's own model as specified by sales leadership. Lesson: where a business has a working forecast model, configure the CRM to it rather than asking the business to adopt the tool's defaults — adoption follows familiarity."),
H2("A capability gap at the licensed tier"),
P("Native churn reporting requires Enterprise; CalcFocus holds Professional. Instead of routing the requirement into a licence upgrade, workarounds were built using calculated properties. Lesson: the partner's first instinct on a tier gap should be engineering, not procurement. Trust earned here is what converted the engagement into a retainer."),
H2("Sequencing training against migration"),
P("Training scheduled before migration would have run on sample records and wasted the session. It was deliberately held until migration completed, so every attendee worked with their own live data. Lesson: training value is a function of data readiness, not calendar convenience."),
H2("Scope discovered mid-flight"),
P("New requirements surfaced continuously once the client saw the platform working. A standing out-of-scope wish list captured them without destabilising the plan or the timeline. Lesson: give mid-engagement scope somewhere legitimate to go, and it stops being a conflict."),

H1("4. Post-Onboarding Strategy"),
P("CalcFocus transitioned directly from onboarding into a retained client success engagement. Weekly client success meetings and monthly strategic reviews are scheduled through December 2026, and 45 of 76 post-onboarding tickets are already closed."),
H2("Immediate next steps for the customer"),
Bullet("Build KPI-driven dashboards and reports against the reporting requirements the team is finalising"),
Bullet("Continue data hygiene on imported records, including domain and association completeness"),
Bullet("Activate the nurture campaign framework with live content"),
Bullet("Work the out-of-scope wish list into a prioritised roadmap"),
Bullet("Extend adoption depth on sequences, task queues and meeting links across the wider sales team"),
];

/* ============ ITEM 2 — PacTec Integration Documentation ============ */
const item2=[...banner("Integration Documentation","PacTec  |  Salesforce and ZoomInfo  |  May – September 2026","ONBOARDING ACCREDITATION — SUBMISSION ITEM 2"),
P("This document profiles two integration use cases delivered for a single customer: a Salesforce integration, and an additional use case using the ZoomInfo marketplace integration."),
callout("Subscription gate — action required before submission",["Submission item 2 requires the profiled customer to hold both Marketing Hub and Sales Hub at Professional or above.","PacTec's Marketing Hub Professional subscription is confirmed. The Sales Hub tier is NOT confirmed, and cannot be assumed: PacTec runs Salesforce as their system of record.","Confirm the Sales Hub tier with the Partner Development Manager before submitting. If PacTec does not hold Sales Hub Professional or above, this item requires a different customer."],"risk"),
new Paragraph({spacing:{after:200},children:[]}),
H1("Engagement Overview"),
kvTable([["Customer","PacTec (pactecinc.com)"],["HubSpot Portal ID","[TO BE INSERTED — customer portal ID]"],["Industry","Business Supplies and Equipment — nuclear and industrial waste packaging"],["Company size","200 employees"],["Location","Clinton, Louisiana, USA"],["Engagement","HubSpot, ZoomInfo and Salesforce Integration — 50 hours"],["Period","May – September 2026"],["Delivery status","70 of 71 scoped tasks complete (98.6%)"],["Subscription","Marketing Hub Professional (confirmed); Sales Hub tier to be confirmed"],["Delivery partner","Quantum Business Solutions"]]),

H1("Use Case 1 — Salesforce Integration"),
H2("Business use case"),
P("PacTec operates a three-system revenue stack: Salesforce as the CRM of record, ZoomInfo for prospect data and buyer intent, and HubSpot for marketing and demand generation. The systems were not exchanging usable data."),
P("Three specific failures defined the problem:"),
Bullet("The Salesforce to HubSpot activity sync had stopped on 5 February 2026 and the cause had never been established. Five months of activity history was not reaching HubSpot."),
Bullet("Deal sync had never been configured at all, so marketing had no visibility of revenue outcomes and no basis for attribution."),
Bullet("Fourteen standard Salesforce integration properties were missing from HubSpot, silently breaking field mapping and reporting."),
P("The business consequence was that marketing could not see what closed, sales could not see marketing context, and neither system could be trusted for reporting."),
H2("Solution description"),
P("The HubSpot–Salesforce integration was designed and configured under a strict constraint: Salesforce remains the system of record. The governing question was therefore not how much data could be synchronised, but what must deliberately not be, so that Salesforce is protected from HubSpot-side noise while marketing gains the revenue visibility it lacked."),
P("Alternatives considered. A middleware or iPaaS layer was assessed and rejected for this use case. The native integration met the object coverage and directional requirements, and inserting middleware between two systems that already had a reliability problem would have added a failure point rather than removed one. Separately, an upgrade to Salesforce integration version 2 was researched and its duplicate-record exposure assessed before any decision was taken, rather than upgrading blind."),
P("A deliberate design decision sits at the centre of the build. Rather than replicating over four hundred ZoomInfo intent fields into Salesforce, a single condensed custom field — HubSpot Summary — was created and mapped, carrying the intent narrative into the Salesforce record where the seller actually works. This traded field sprawl for usable context, and was validated with live test contacts before release."),
H2("Data flow diagram"),
new Paragraph({spacing:{after:120},alignment:AlignmentType.CENTER,children:[new ImageRun({type:"png",data:img,transformation:{width:660,height:406}})]}),
P("Figure 1 — PacTec integration architecture. ZoomInfo supplies intent and prospect data into HubSpot's property model; HubSpot clusters, scores and routes it; and HubSpot exchanges records bidirectionally with Salesforce, which remains the system of record.",{size:18,color:GREY,italics:true,align:AlignmentType.CENTER}),
H2("Object coverage and sync direction"),
gridTable(["Object","HubSpot to Salesforce","Salesforce to HubSpot","Notes"],[
["Contacts","Yes","Yes","Bidirectional with selective sync rules"],
["Leads","Yes","—","Qualified leads carrying the HubSpot Summary field"],
["Deals / Opportunities","—","Yes","Newly wired; previously not configured"],
["Tasks","Yes","—","Intent-triggered creation with dual routing"],
["Activities","—","Yes","Restored after outage, plus historical backfill"]],[2400,2600,2600,2840]),
new Paragraph({spacing:{after:180},children:[]}),
H2("How the integration was used"),
Bullet("Connector installed and object alignment defined across contacts, leads, deals, tasks and activities"),
Bullet("Field mapping, sync rules and inclusion criteria configured"),
Bullet("Selective sync configured with explicit decisions on what must not synchronise"),
Bullet("Pipeline stages aligned between the two systems"),
Bullet("Salesforce-sourced HubSpot properties created, and fourteen missing standard integration properties gap-filled"),
Bullet("The 5 February 2026 sync failure root-caused and the Salesforce to HubSpot activity sync restored"),
Bullet("Salesforce to HubSpot deal sync wired for the first time"),
Bullet("Historical Salesforce activity data imported into HubSpot to backfill the outage gap"),
Bullet("HubSpot to Salesforce task creation investigated, remediated and extended to dual routing for intent triggers"),
Bullet("Custom HubSpot Summary field mapped and validated end to end with live test contacts"),
H2("Results and achieved benefits"),
callout("TO COMPLETE BEFORE SUBMISSION",["HubSpot requires quantified improvements here: efficiency, data accuracy, conversion rates or cost savings.","Suggested measures: activity records backfilled; sync error rate before and after; opportunities now visible in HubSpot that previously were not; seller response time to intent-triggered tasks.","Capture at the next monthly strategic review with Katie Lanoix and Christina Reckard."],"gap"),

H1("Use Case 2 — ZoomInfo Marketplace Integration"),
H2("Business use case"),
P("PacTec was paying for ZoomInfo buyer intent data that could not reach a seller. There was no property model in HubSpot to receive the signals, no segmentation to act on them, no alerting, and no path from an intent spike to a Salesforce opportunity. The spend could not be justified because no line connected a signal to revenue."),
H2("Solution description"),
P("The ZoomInfo marketplace integration was deployed together with a purpose-built HubSpot property and workflow architecture designed to make intent operationally usable. A clustering model was layered on top so that sellers receive coherent themes rather than forty-seven separate signal types."),
H2("How the integration was used"),
gridTable(["Component","Built"],[
["Intent property model","47 intent topics deployed as 423 HubSpot properties — five properties for each of 48 contact-level signals, plus four company-level properties"],
["Data export","Automated ZoomInfo to HubSpot export configured; the same property model then replicated into Salesforce alongside the client's administrator"],
["Targeting","ZoomInfo saved searches aligned to the defined ideal customer profile"],
["Alerting","Intent signal to HubSpot workflow to real-time sales alert chain"],
["Cross-system path","ZoomInfo prospect to HubSpot lead to Salesforce opportunity workflow, tested end to end with dummy contacts before go-live"],
["Personas","Five personas with properties, segments and workflows: Head of Organization, Head of Operations, Head of Procurement, Industrial Waste Management, Nuclear Waste Management"],
["Clustering","30 intent cluster lists — 15 marketing email and 15 master; Facilities Management activated as the pilot cluster"],
["Commercial governance","ZoomInfo subscription audited for seats against bulk credits; account-level intent delivery escalated to ZoomInfo support"],
["Reporting","Intent dashboard covering volume, clusters and customer versus non-customer, plus an intent-to-revenue attribution process"]],[2600,7840]),
new Paragraph({spacing:{after:200},children:[]}),
H2("Results and achieved benefits"),
callout("TO COMPLETE BEFORE SUBMISSION",["Suggested measures: intent-sourced pipeline value; alerts generated per period; opportunities attributed to intent triggers; seller response time; ZoomInfo credit efficiency after the subscription audit."],"gap"),

H1("Supporting Delivery Record"),
gridTable(["Phase","Tasks","Complete"],[
["Phase 0 — Kick-Off and Discovery","19","19 (100%)"],
["Phase 1 — HubSpot Foundational Configuration","8","8 (100%)"],
["Phase 2 — Contact and List Import, Lifecycle, MQL/SQL","7","7 (100%)"],
["Phase 3 — Marketing Hub Configuration","12","12 (100%)"],
["Phase 4 — ZoomInfo and HubSpot Integration","7","7 (100%)"],
["Phase 5 — Salesforce and HubSpot Integration","9","9 (100%)"],
["Phase 6 — Revenue Efficiency Model Build","4","4 (100%)"],
["Phase 7 — Training and Wrap-Up","5","4 (80%)"],
["TOTAL","71","70 (98.6%)"]],[6040,2200,2200]),
new Paragraph({spacing:{after:180},children:[]}),
P("Discovery included a full technical audit across website, email, HubSpot, ZoomInfo and Salesforce, with PacTec's Salesforce administrator exporting a complete field inventory before any mapping work began. Engagement record: 28 calls, approximately 115 logged emails, 22 tickets, 37 meetings and 21 transcripts."),
callout("Open delivery item",["One task remains open: QA and Go-Live Readiness Review (Phase 7). Closing it before submission presents a 100% complete plan rather than 98.6%."],"gap"),
];

const jobs=[["QBS-Onboarding-Item1-CalcFocus-OBO-Project-Plan.docx",item1],["QBS-Onboarding-Item2-PacTec-Integration-Documentation.docx",item2],["QBS-Onboarding-Item3-CalcFocus-Project-Review.docx",item3]];
(async()=>{for(const [name,children] of jobs){const b=await Packer.toBuffer(makeDoc(children));fs.writeFileSync(name,b);console.log("wrote",name,b.length);}})();
