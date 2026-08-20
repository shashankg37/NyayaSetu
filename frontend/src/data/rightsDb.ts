export interface RightsSection {
  heading: string;
  text: string;
  citations?: string[];
}

export interface RightsData {
  title: string;
  sections: RightsSection[];
}

export const rightsDb: Record<string, Record<string, RightsData>> = {
  woman: {
    employment: {
      title: 'Workplace Rights for Women',
      sections: [
        { heading: 'Your Right', text: 'Under the Equal Remuneration Act, 1976 and the Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013, you have the right to equal pay for equal work and a workplace free from sexual harassment.' },
        { heading: 'Your Remedy', text: 'If you are denied equal pay or subjected to sexual harassment, you may file a complaint with the Labour Commissioner under the Equal Remuneration Act or with the Internal Complaints Committee (ICC) constituted under the POSH Act, 2013. In the absence of an ICC, you may approach the Local Complaints Committee (LCC) at the District level.' },
        { heading: 'What To Do', text: 'Document every instance of unequal pay or harassment in writing with dates, witnesses, and evidence such as messages or emails. Approach your employer\'s ICC within three months of the incident. If the employer fails to constitute an ICC or you face retaliation, file a complaint with the LCC or lodge an FIR at the nearest police station under Section 354 or Section 376 of the Indian Penal Code for criminal offences.' },
        { heading: 'Where To Go', citations: ['Equal Remuneration Act, 1976 — Section 4', 'POSH Act, 2013 — Section 9', 'Indian Penal Code, 1860 — Section 354'] }
      ]
    },
    land: {
      title: 'Property Rights of Women',
      sections: [
        { heading: 'Your Right', text: 'Under the Hindu Succession (Amendment) Act, 2005, a daughter has an equal coparcenary right in Hindu ancestral property, identical to that of a son. This right exists by birth and cannot be denied by any family custom or Will. For self-acquired property, you have full testamentary rights as an heir under the Indian Succession Act, 1925.' },
        { heading: 'Your Remedy', text: 'If your coparcenary or inheritance rights are denied, you may file a suit for partition and separate possession in the appropriate civil court. If you are a Muslim woman, your rights to dower (mahr) and maintenance are protected under Muslim Women (Protection of Rights on Divorce) Act, 1986 and Section 125 of the CrPC as upheld in Shah Bano and subsequent cases.' },
        { heading: 'What To Do', text: 'Gather documents proving your relationship (birth certificate, Aadhaar), the property records (sale deed, revenue records), and any Will or succession certificate. Consult a civil lawyer to file a partition suit under Order IV of the Code of Civil Procedure, 1908. Apply for interim protection if there is a risk of alienation of the property.' },
        { heading: 'Where To Go', citations: ['Hindu Succession (Amendment) Act, 2005 — Section 6', 'Indian Succession Act, 1925 — Sections 32-49', 'CPC, 1908 — Order IV'] }
      ]
    },
    family: {
      title: 'Family & Matrimonial Rights for Women',
      sections: [
        { heading: 'Your Right', text: 'Under Section 125 of the Code of Criminal Procedure, 1973 and the Protection of Women from Domestic Violence Act, 2005, you have the right to maintenance, protection from domestic violence, and residence in the shared household.' },
        { heading: 'Your Remedy', text: 'You may file an application for maintenance under Section 125 CrPC in the Magistrate\'s court, or seek protection and residence orders under the DV Act. For cruelty or dowry demands, you may file a complaint under Section 498A IPC.' },
        { heading: 'What To Do', text: 'If facing domestic violence, call the Women Helpline (181) or Police (100). Record evidence of abuse and maintain a safety plan. Apply for a protection order under Section 12 of the DV Act through the nearest Magistrate\'s court. For maintenance, file under Section 125 CrPC with proof of income of the husband and your financial need.' },
        { heading: 'Where To Go', citations: ['DV Act, 2005 — Section 12', 'CrPC, 1973 — Section 125', 'IPC, 1860 — Section 498A'] }
      ]
    },
    housing: {
      title: 'Housing Rights for Women',
      sections: [
        { heading: 'Your Right', text: 'Under the Real Estate (Regulation and Development) Act, 2016, you are protected against unfair practices by builders. As a homebuyer, you have the right to possession on time and information about the project. Women-headed households are also entitled to priority under many state housing schemes.' },
        { heading: 'Your Remedy', text: 'If a builder defaults on delivery or misleads you, you may file a complaint with the Real Estate Regulatory Authority (RERA) in your state. You may also seek compensation under the Consumer Protection Act, 2019 for deficiency in service.' },
        { heading: 'What To Do', text: 'Register your complaint with the state RERA authority online or in person. Preserve all agreements, advertisements, and payment receipts. If the builder has not registered the project, report it to the RERA authority for penalty proceedings. For illegal eviction by a landlord, approach the local Rent Control Court or file a suit for injunction under CPC.' },
        { heading: 'Where To Go', citations: ['RERA Act, 2016 — Section 14, 18, 31', 'Consumer Protection Act, 2019 — Section 2(11)'] }
      ]
    },
    money: {
      title: 'Financial Rights for Women',
      sections: [
        { heading: 'Your Right', text: 'Under the Protection of Women from Domestic Violence Act, 2005, you have the right to claim monetary relief for expenses incurred as a result of domestic violence. You also have the right to equal financial treatment under banking and credit regulations.' },
        { heading: 'Your Remedy', text: 'You may apply for monetary relief under Section 20 of the DV Act. For financial fraud or exploitation, file a complaint under the Indian Penal Code and approach the consumer forum for banking irregularities.' },
        { heading: 'What To Do', text: 'Maintain records of all financial transactions and assets. If facing financial abuse, open an individual bank account in your name. Approach the Legal Services Authority under the Legal Services Authorities Act, 1987 for free legal aid. For debt recovery harassment by banks, file a complaint with the Banking Ombudsman under RBI guidelines.' },
        { heading: 'Where To Go', citations: ['DV Act, 2005 — Section 20', 'Legal Services Authorities Act, 1987 — Section 12', 'RBI Banking Ombudsman Scheme, 2006'] }
      ]
    },
    safety: {
      title: 'Safety Rights for Women',
      sections: [
        { heading: 'Your Right', text: 'Under Section 354 of the Indian Penal Code, the Immoral Traffic (Prevention) Act, 1956, and the IT Act, 2000, you have the right to be free from physical, sexual, and digital assault.' },
        { heading: 'Your Remedy', text: 'For any form of assault, you may file an FIR at the nearest police station. The police are duty-bound to register the FIR under Section 154 CrPC and cannot refuse. For online harassment, you may file a complaint under Section 66A (cyberstalking) and Section 67 (obscenity) of the IT Act.' },
        { heading: 'What To Do', text: 'Dial 100 for immediate police assistance or 181 (Women Helpline). Preserve all evidence including screenshots, medical records, and witness statements. You have the right to register an FIR at any police station regardless of jurisdiction under zero FIR provisions. Request a female officer for recording your statement under Section 161 CrPC.' },
        { heading: 'Where To Go', citations: ['IPC, 1860 — Section 354', 'CrPC, 1973 — Section 154', 'IT Act, 2000 — Section 66A, 67'] }
      ]
    }
  },
  farmer: {
    employment: {
      title: 'Employment & Labour Rights for Farmers',
      sections: [
        { heading: 'Your Right', text: 'Under the National Food Security Act, 2013, you have the right to receive minimum support price (MSP) for notified crops. The Agricultural Produce Market Committee (APMC) Acts in various states protect farmers from exploitation by middlemen.' },
        { heading: 'Your Remedy', text: 'If your produce is purchased below MSP or you face exploitation in mandis, you may file a complaint with the District Magistrate or the state APMC authority. For crop insurance disputes, approach the Grievance Redressal Officer under PM Fasal Bima Yojana.' },
        { heading: 'What To Do', text: 'Register as a farmer with the local APMC and obtain a valid license. Maintain records of all sales and weight slips. For MSP-related grievances, file a complaint with the Food Corporation of India (FCI) procurement centre. If market access is denied, approach the District Collector under the Essential Commodities Act, 1955.' },
        { heading: 'Where To Go', citations: ['NFSA, 2013 — Section 3', 'APMC Act (State)', 'Essential Commodities Act, 1955 — Section 3'] }
      ]
    },
    land: {
      title: 'Land Rights for Farmers',
      sections: [
        { heading: 'Your Right', text: 'Under the Land Acquisition, Rehabilitation and Resettlement Act, 2013 (LARR Act), you have the right to fair compensation at four times the market value for rural land, consent of 80% of affected families, and a mandatory Social Impact Assessment before acquisition.' },
        { heading: 'Your Remedy', text: 'If your land is acquired without following due process or without fair compensation, you may challenge the acquisition under Section 24 of the LARR Act. You may approach the District Collector or the Land Acquisition, Rehabilitation and Resettlement Authority.' },
        { heading: 'What To Do', text: 'Maintain updated land records including 7/12 extract (Maharashtra) or equivalent revenue records. If a notice under Section 11 of the LARR Act is issued, respond within the stipulated time. Engage a lawyer to verify compliance with the R&R scheme. For encroachment, file a police complaint under Section 441 IPC.' },
        { heading: 'Where To Go', citations: ['LARR Act, 2013 — Section 24, 26, 29', 'IPC, 1860 — Section 441'] }
      ]
    },
    family: {
      title: 'Family & Succession Rights for Farmers',
      sections: [
        { heading: 'Your Right', text: 'Under the Hindu Succession Act, 1956, agricultural land is part of the estate subject to intestate succession. The state-specific tenancy laws also protect the rights of tillers and sharecroppers.' },
        { heading: 'Your Remedy', text: 'If your inheritance rights to agricultural land are denied, file a suit for partition in the civil court. For tenancy disputes, approach the Tenancy Court or Revenue Authority under the relevant state tenancy act.' },
        { heading: 'What To Do', text: 'Obtain a certified copy of the revenue records showing your name as a co-sharer or tenant. File an application for mutation of land records in the Tahsildar office under Section 89 of the Maharashtra Land Revenue Code or equivalent. For disputes, apply for a certificate of inheritance from the Tehsildar.' },
        { heading: 'Where To Go', citations: ['Hindu Succession Act, 1956 — Section 8, 9', 'State Tenancy Act', 'Land Revenue Code — Section 89'] }
      ]
    },
    housing: {
      title: 'Housing & Shelter Rights for Farmers',
      sections: [
        { heading: 'Your Right', text: 'Under the Pradhan Mantri Awaas Yojana (Gramin), rural households below the poverty line have the right to receive housing assistance of up to Rs 1.20 lakh. The Mahatma Gandhi National Rural Employment Guarantee Act, 2005 also provides for housing construction as permissible work.' },
        { heading: 'Your Remedy', text: 'If you have been denied housing benefits under PMAY-G despite being eligible, file a grievance with the Panchayat or the District Programme Coordinator. For landless agricultural labourers, demand allocation under the Landless Housing schemes.' },
        { heading: 'What To Do', text: 'Apply through the Gram Panchayat with your BPL certificate, Aadhaar, and bank details. Track your application through the PMAY-G portal. For MGNREGA housing work, demand 100 days of guaranteed employment through the Gram Panchayat under Section 6(1) of the Act.' },
        { heading: 'Where To Go', citations: ['PMAY-G — Operational Guidelines', 'MGNREGA, 2005 — Section 6(1)'] }
      ]
    },
    money: {
      title: 'Financial Rights for Farmers',
      sections: [
        { heading: 'Your Right', text: 'Under the Interest Subvention Scheme, you have the right to short-term crop loans at 4% per annum. The Kisan Credit Card (KCC) scheme provides hassle-free credit. The Farmers (Empowerment and Protection) Agreement on Price Assurance Act, 2013 protects against exploitation in contract farming.' },
        { heading: 'Your Remedy', text: 'If your loan is classified as NPAs unfairly or you face coercive recovery by banks, file a complaint with the Banking Ombudsman under RBI guidelines. For crop insurance claims denied under PMFBY, approach the district-level Grievance Redressal Officer.' },
        { heading: 'What To Do', text: 'Apply for a KCC through your nearest bank branch with land records and identity proof. For loan-related disputes, approach the District Lead Bank Manager. For coercive recovery, send a written complaint to the Bank\'s Regional Manager and the Banking Ombudsman. Maintain records of all loan transactions and crop loss evidence for insurance claims.' },
        { heading: 'Where To Go', citations: ['Interest Subvention Scheme, 2024', 'RBI Banking Ombudsman Scheme', 'PMFBY, 2016 — Section 10'] }
      ]
    },
    safety: {
      title: 'Safety Rights for Farmers',
      sections: [
        { heading: 'Your Right', text: 'Under the Essential Commodities Act, 1955 and the Farmers\' Produce Trade and Commerce Act, 2020, you have the right to sell your produce freely without exploitation. The Prevention of Damage to Public Property Act, 1984 protects your property.' },
        { heading: 'Your Remedy', text: 'If your produce is forcibly seized or destroyed, file an FIR under Section 425 IPC (mischief) and the Essential Commodities Act. For threats or violence related to land or crop disputes, approach the Superintendent of Police under Section 154 CrPC.' },
        { heading: 'What To Do', text: 'Report any incident of crop destruction or produce seizure to the police immediately. Photograph and video-document the damage with witnesses. File a complaint with the District Magistrate for immediate relief under the Disaster Management Act if the damage is due to natural causes and insurance claims are being delayed.' },
        { heading: 'Where To Go', citations: ['IPC, 1860 — Section 425', 'Essential Commodities Act, 1955', 'CrPC, 1973 — Section 154'] }
      ]
    }
  },
  worker: {
    employment: {
      title: 'Labour Rights for Workers',
      sections: [
        { heading: 'Your Right', text: 'Under the Code on Wages, 2019, you have the right to receive minimum wage, overtime pay, and timely payment. The Employees\' Provident Funds Act, 1952 provides for provident fund contributions. The Occupational Safety, Health and Working Conditions Code, 2020 ensures a safe workplace.' },
        { heading: 'Your Remedy', text: 'For non-payment or underpayment of wages, file a complaint with the Labour Commissioner. For EPF violations, approach the EPFO Commissioner. For workplace safety violations, complain to the Inspector-cum-Facilitator under the OSH Code.' },
        { heading: 'What To Do', text: 'Maintain your employment contract, salary slips, and attendance records. If wages are unpaid for more than the stipulated period, send a legal notice under Section 7 of the Payment of Wages Act, 1936. For retrenchment without notice, claim compensation under Section 25F of the Industrial Disputes Act, 1947. Register a complaint with the Labour Commissioner\'s office with supporting documents.' },
        { heading: 'Where To Go', citations: ['Code on Wages, 2019 — Section 12', 'EPF Act, 1952 — Section 7', 'Industrial Disputes Act, 1947 — Section 25F'] }
      ]
    },
    land: {
      title: 'Land Rights for Workers',
      sections: [
        { heading: 'Your Right', text: 'Under the State tenancy and land reform laws, you have rights as an agricultural tenant or sharecropper. The Land Ceiling Acts in various states prevent concentration of land.' },
        { heading: 'Your Remedy', text: 'If you are evicted from land you till, approach the Revenue Authority under the relevant state tenancy act. For land ceiling violations, file a complaint with the Land Ceiling Officer.' },
        { heading: 'What To Do', text: 'Obtain a copy of your tenancy agreement or evidence of cultivation from the village revenue officer. Apply for registration as a tenant under the relevant state act. For disputes, approach the Tehsildar or the Tenancy Court.' },
        { heading: 'Where To Go', citations: ['State Tenancy Act', 'Land Ceiling Act (State)', 'Revenue Code — Section 89'] }
      ]
    },
    family: {
      title: 'Family Rights for Workers',
      sections: [
        { heading: 'Your Right', text: 'Under the Employees\' State Insurance Act, 1948, you and your dependants are entitled to medical, sickness, and maternity benefits. The Maternity Benefit Act, 1961 provides 26 weeks of paid maternity leave for eligible women workers.' },
        { heading: 'Your Remedy', text: 'For denial of ESI benefits, file a complaint with the ESI Corporation. For maternity benefit denial, complain to the Inspector under the Maternity Benefit Act. For provident fund withdrawal issues, approach the EPFO.' },
        { heading: 'What To Do', text: 'Ensure your employer has registered you under ESI with a valid insurance number. For maternity benefit, submit a medical certificate to your employer 8 weeks before expected delivery. If benefits are denied, approach the ESI Dispensary or Hospital directly for medical treatment. For provident fund issues, check your UAN on the EPFO portal.' },
        { heading: 'Where To Go', citations: ['ESI Act, 1948 — Section 50', 'Maternity Benefit Act, 1961 — Section 5', 'EPF Act, 1952 — Section 7'] }
      ]
    },
    housing: {
      title: 'Housing Rights for Workers',
      sections: [
        { heading: 'Your Right', text: 'Under the Building and Other Construction Workers Act, 1996, registered construction workers are entitled to housing assistance from the Building Workers\' Welfare Board. Migrant workers in certain states are entitled to employer-provided housing under the OSH Code.' },
        { heading: 'Your Remedy', text: 'If your employer fails to provide mandated housing or shelter allowance, file a complaint with the Labour Commissioner. For BOC Board housing benefits, apply to your state Building Workers\' Welfare Board.' },
        { heading: 'What To Do', text: 'Register as a construction worker with your state BOC Welfare Board with proof of employment and identity. Apply for housing assistance through the Board. For employer-provided housing, ensure your employment contract specifies the terms. For migrant worker issues, approach the Interstate Migrant Workmen provisions under the OSH Code.' },
        { heading: 'Where To Go', citations: ['BOC Act, 1996 — Section 22', 'OSH Code, 2020 — Section 51'] }
      ]
    },
    money: {
      title: 'Financial Rights for Workers',
      sections: [
        { heading: 'Your Right', text: 'Under the Payment of Wages Act, 1936, you have the right to receive wages on time without deductions except as permitted by law. The Employees\' Provident Funds Act, 1952 entitles you to employer contributions towards provident fund.' },
        { heading: 'Your Remedy', text: 'For wage delays, file a complaint with the Labour Commissioner within 6 months. For EPF default by employer, file a complaint with the EPFO. For gratuity denial, approach the Controlling Authority under the Payment of Gratuity Act, 1972.' },
        { heading: 'What To Do', text: 'Maintain your salary slips and bank statements as evidence. For unpaid wages, send a written demand to your employer. If no response within 15 days, file a complaint under Section 15 of the Payment of Wages Act with the Labour Commissioner. For EPF issues, use the EPFiGMS grievance portal or file a complaint with the Regional EPFO Commissioner.' },
        { heading: 'Where To Go', citations: ['Payment of Wages Act, 1936 — Section 15', 'EPF Act, 1952 — Section 7A', 'Gratuity Act, 1972 — Section 7'] }
      ]
    },
    safety: {
      title: 'Safety Rights for Workers',
      sections: [
        { heading: 'Your Right', text: 'Under the Occupational Safety, Health and Working Conditions Code, 2020, you have the right to a safe workplace, adequate safety equipment, and training. The Factories Act, 1948 mandates provisions for health and safety in factories.' },
        { heading: 'Your Remedy', text: 'For workplace safety violations, file a complaint with the Inspector-cum-Facilitator under the OSH Code. For factory accidents, report to the Factories Inspector and file for compensation under the Workmen\'s Compensation Act, 1923.' },
        { heading: 'What To Do', text: 'Report unsafe conditions to your employer in writing and keep a copy. If the employer does not act, file a complaint with the Inspector-cum-Facilitator online or in person. For workplace accidents, file an FIR and simultaneously apply for compensation under the Workmen\'s Compensation Act. For occupational diseases, get a medical certificate and report to the employer within 7 days.' },
        { heading: 'Where To Go', citations: ['OSH Code, 2020 — Section 36', 'Factories Act, 1948 — Section 7A', 'Workmen\'s Compensation Act, 1923 — Section 3'] }
      ]
    }
  },
  senior: {
    employment: {
      title: 'Employment & Pension Rights for Senior Citizens',
      sections: [
        { heading: 'Your Right', text: 'Under the Maintenance and Welfare of Parents and Senior Citizens Act, 2007, you have the right to claim maintenance from your children or legal heirs. The Employment Provident Fund Act, 1952 entitles you to your provident fund upon retirement.' },
        { heading: 'Your Remedy', text: 'For non-payment of PF, approach the EPFO Commissioner under Section 7A of the EPF Act. For maintenance claims, file an application with the Maintenance Tribunal under Section 5 of the Senior Citizens Act.' },
        { heading: 'What To Do', text: 'Collect your PF and pension documents from your former employer. Submit Form 19 and Form 10C to the EPFO for settlement. For maintenance, file an application before the Maintenance Tribunal (District Magistrate or Additional District Magistrate) with proof of your financial need and the respondent\'s income.' },
        { heading: 'Where To Go', citations: ['EPF Act, 1952 — Section 7A', 'Senior Citizens Act, 2007 — Section 5'] }
      ]
    },
    land: {
      title: 'Property Rights for Senior Citizens',
      sections: [
        { heading: 'Your Right', text: 'Under the Maintenance and Welfare of Parents and Senior Citizens Act, 2007, property transfers made for maintenance can be voided if the transferee fails to provide maintenance. You also have full property rights under the Transfer of Property Act, 1882.' },
        { heading: 'Your Remedy', text: 'If a property transferred on condition of maintenance is not being maintained, file an application with the Maintenance Tribunal to declare the transfer void. For property disputes, file a civil suit for partition or injunction.' },
        { heading: 'What To Do', text: 'Preserve all property documents and records of the transfer deed. If property was transferred with conditions, obtain a copy of the deed and file an application under Section 23 of the Senior Citizens Act. For matters requiring urgent relief, apply for an interim injunction under Order XXXIX of CPC.' },
        { heading: 'Where To Go', citations: ['Senior Citizens Act, 2007 — Section 23', 'Transfer of Property Act, 1882 — Section 10', 'CPC, 1908 — Order XXXIX'] }
      ]
    },
    family: {
      title: 'Family Maintenance Rights for Senior Citizens',
      sections: [
        { heading: 'Your Right', text: 'Under the Maintenance and Welfare of Parents and Senior Citizens Act, 2007, you are entitled to receive maintenance of up to Rs 10,000 per month from your children, grandchildren, or legal heirs who are in possession of your property. The right to shelter, food, and medical care is fundamental under Articles 21 and 46 of the Constitution.' },
        { heading: 'Your Remedy', text: 'File an application before the Maintenance Tribunal under Section 5 of the Senior Citizens Act. The Tribunal can order monthly maintenance of up to Rs 10,000 and can even void property transfers made for maintenance. For criminal neglect, an FIR can be lodged under Section 4 of the Senior Citizens Act.' },
        { heading: 'What To Do', text: 'Gather evidence of your financial need and the respondent\'s income (property records, bank statements). File an application before the Maintenance Tribunal through the District Magistrate\'s office. The Tribunal must dispose of the case within 90 days. For urgent situations, contact the local police or the helpline for senior citizens.' },
        { heading: 'Where To Go', citations: ['Senior Citizens Act, 2007 — Section 5, 9', 'Indian Penal Code, 1860 — Section 4', 'Constitution of India — Article 21'] }
      ]
    },
    housing: {
      title: 'Housing Rights for Senior Citizens',
      sections: [
        { heading: 'Your Right', text: 'Under the Senior Citizens Act, 2007, you have the right to be maintained in your shared household. The Right to Fair Compensation and Transparency in Land Acquisition Act, 2013 protects your land from acquisition without proper rehabilitation.' },
        { heading: 'Your Remedy', text: 'If your children refuse to vacate your property, file a suit for eviction under CPC. For age-friendly housing schemes, apply through the Ministry of Social Justice and Empowerment or the state Department of Social Welfare.' },
        { heading: 'What To Do', text: 'If facing eviction or refusal to vacate by relatives, file an FIR under Section 441 IPC for criminal trespass and simultaneously file a civil suit for injunction and eviction. For government housing schemes for senior citizens, contact the District Social Welfare Officer with your age proof and income certificate.' },
        { heading: 'Where To Go', citations: ['Senior Citizens Act, 2007', 'CPC, 1908 — Section 9', 'IPC, 1860 — Section 441'] }
      ]
    },
    money: {
      title: 'Financial Rights for Senior Citizens',
      sections: [
        { heading: 'Your Right', text: 'Under the Senior Citizens Act, 2007, you have the right to financial maintenance. Banks provide higher interest rates on fixed deposits for senior citizens. The Reserve Bank of India mandates that banks cannot charge foreclosure penalties on floating-rate home loans.' },
        { heading: 'Your Remedy', text: 'For financial exploitation by relatives or caretakers, file a complaint with the police under Section 420 IPC (cheating) and with the Maintenance Tribunal. For banking issues, approach the Banking Ombudsman under RBI guidelines.' },
        { heading: 'What To Do', text: 'Register for Senior Citizen savings schemes at your bank with age proof. If facing financial exploitation, change your bank account and add a trusted person for joint operations. For quick grievance redressal, use the RBI\'s Sachet portal for unauthorized lending complaints. For urgent financial distress, approach the District Legal Services Authority for free legal aid.' },
        { heading: 'Where To Go', citations: ['Senior Citizens Act, 2007', 'RBI Banking Ombudsman Scheme', 'Legal Services Authorities Act, 1987'] }
      ]
    },
    safety: {
      title: 'Safety Rights for Senior Citizens',
      sections: [
        { heading: 'Your Right', text: 'Under the Maintenance and Welfare of Parents and Senior Citizens Act, 2007, you have the right to be free from abuse and neglect. Section 3 of the Act makes it an offence to abandon or neglect senior citizens. The Indian Penal Code provides for punishment for assault and intimidation.' },
        { heading: 'Your Remedy', text: 'For abuse or neglect, file a complaint with the Maintenance Tribunal under the Senior Citizens Act. For physical assault, file an FIR under Section 323 IPC. For mental cruelty, approach the police under Section 498A IPC. Senior citizens can also call Elderline (14567) for immediate help.' },
        { heading: 'What To Do', text: 'Call 14567 (Elderline) for immediate assistance. Document the abuse with photographs, medical records, and witness statements. File a complaint with the local police station and the Maintenance Tribunal. For urgent shelter, contact the state-run old age homes or the District Social Welfare Officer.' },
        { heading: 'Where To Go', citations: ['Senior Citizens Act, 2007 — Section 3, 4', 'IPC, 1860 — Section 323', 'Elderline: 14567'] }
      ]
    }
  },
  consumer: {
    employment: {
      title: 'Consumer Rights in Employment Services',
      sections: [
        { heading: 'Your Right', text: 'Under the Consumer Protection Act, 2019, services including banking, insurance, telecommunications, and transport are covered. If you have paid for a service and it is deficient, you are entitled to compensation under the Act.' },
        { heading: 'Your Remedy', text: 'For deficient services, file a complaint with the District Consumer Disputes Redressal Forum (for claims up to Rs 1 crore), the State Commission (Rs 1-10 crore), or the National Commission (above Rs 10 crore). You may also file online through the E-Daakhil portal.' },
        { heading: 'What To Do', text: 'Gather all evidence: bills, receipts, correspondence, and advertisements. File a written complaint with the appropriate consumer forum with particulars of the deficiency. You may also file online through edaakhil.nic.in. The forum must dispose of the complaint within 3 months from receipt of notice by the opposite party.' },
        { heading: 'Where To Go', citations: ['Consumer Protection Act, 2019 — Section 34, 35, 36', 'E-Daakhil Portal: edaakhil.nic.in'] }
      ]
    },
    land: {
      title: 'Consumer Rights in Real Estate',
      sections: [
        { heading: 'Your Right', text: 'Under RERA (Real Estate Regulation and Development Act, 2016) and the Consumer Protection Act, 2019, homebuyers are protected against delays, defective construction, and misleading advertisements by builders.' },
        { heading: 'Your Remedy', text: 'File a complaint with the state RERA authority for delay in possession or deviation from sanctioned plans. You may also file a consumer complaint for deficiency in service under the Consumer Protection Act.' },
        { heading: 'What To Do', text: 'Register your complaint with the state RERA authority through their online portal. Attach the agreement, payment receipts, and evidence of the builder\'s default. For consumer complaints, file through the E-Daakhil portal with the builder\'s response and your evidence. Simultaneously, you may approach the Real Estate Appellate Tribunal for relief.' },
        { heading: 'Where To Go', citations: ['RERA Act, 2016 — Section 14, 18, 31', 'Consumer Protection Act, 2019 — Section 34'] }
      ]
    },
    family: {
      title: 'Consumer Rights in Family Services',
      sections: [
        { heading: 'Your Right', text: 'Under the Consumer Protection Act, 2019, services by healthcare providers, educational institutions, and insurance companies are covered. You have the right to seek compensation for deficiency in such services.' },
        { heading: 'Your Remedy', text: 'For medical negligence, file a complaint with the National Consumer Disputes Redressal Commission or the State Commission depending on the claim amount. For insurance claim denials, file through the E-Daakhil portal.' },
        { heading: 'What To Do', text: 'For medical negligence, obtain all medical records under the Clinical Establishments Act. File a complaint within 2 years of the deficiency with the appropriate consumer forum. For insurance denials, send a written representation to the Insurance Ombudsman within 30 days of rejection. Preserve all correspondence and documents.' },
        { heading: 'Where To Go', citations: ['Consumer Protection Act, 2019 — Section 34', 'Clinical Establishments Act, 2010', 'Insurance Ombudsman'] }
      ]
    },
    housing: {
      title: 'Consumer Rights in Housing Services',
      sections: [
        { heading: 'Your Right', text: 'Under the Consumer Protection Act, 2019, homebuyers are consumers and have the right to seek compensation for deficiency in housing services including maintenance, water supply, and common area upkeep by builders or housing societies.' },
        { heading: 'Your Remedy', text: 'For deficiency in services by housing societies or builders, file a consumer complaint. For maintenance disputes, approach the Consumer Forum for compensation and directions. You may also approach the Registrar of Societies for society-related disputes.' },
        { heading: 'What To Do', text: 'Document the deficiency with photographs, written complaints, and maintenance records. Send a legal notice to the builder or housing society secretary. If no resolution within 30 days, file a consumer complaint through the E-Daakhil portal or in person at the appropriate consumer forum.' },
        { heading: 'Where To Go', citations: ['Consumer Protection Act, 2019 — Section 2(42)', 'E-Daakhil Portal'] }
      ]
    },
    money: {
      title: 'Consumer Rights in Financial Services',
      sections: [
        { heading: 'Your Right', text: 'Under the Consumer Protection Act, 2019 and RBI guidelines, you have the right to fair banking, transparent insurance terms, and protection against unfair trade practices in financial services. The RBI mandates banks to display all charges upfront.' },
        { heading: 'Your Remedy', text: 'For banking complaints, first approach the Banking Ombudsman. For insurance complaints, approach the Insurance Ombudsman. For other financial services, file a consumer complaint. You may also report to SEBI for securities-related issues.' },
        { heading: 'What To Do', text: 'File a written complaint with the bank\'s Nodal Officer first. If unresolved within 30 days, approach the Banking Ombudsman. For insurance, file with the Insurance Ombudsman within 30 days of the insurer\'s final reply. Maintain all policy documents, correspondence, and evidence of financial loss.' },
        { heading: 'Where To Go', citations: ['Consumer Protection Act, 2019', 'RBI Banking Ombudsman Scheme', 'Insurance Ombudsman — Insurance Act, 1938'] }
      ]
    },
    safety: {
      title: 'Consumer Safety Rights',
      sections: [
        { heading: 'Your Right', text: 'Under the Consumer Protection Act, 2019, you have the right to be protected against goods and services that are hazardous to life and property. The Bureau of Indian Standards Act, 2016 ensures product safety standards.' },
        { heading: 'Your Remedy', text: 'For product liability claims, file a complaint under Chapter VI of the Consumer Protection Act, 2019. For defective products causing injury, file for product liability with the appropriate consumer forum. Report unsafe products to the Central Consumer Protection Authority (CCPA).' },
        { heading: 'What To Do', text: 'Preserve the defective product and all purchase evidence. File a complaint with the CCPA for product safety violations. For compensation, file a product liability claim under Section 83 of the Consumer Protection Act. For medical devices or drugs, report to the Drug Controller General of India.' },
        { heading: 'Where To Go', citations: ['Consumer Protection Act, 2019 — Section 83, 87', 'BIS Act, 2016 — Section 31', 'Drug and Cosmetics Act, 1940'] }
      ]
    }
  },
  student: {
    employment: {
      title: 'Rights of Students in Employment',
      sections: [
        { heading: 'Your Right', text: 'Under the Equal Opportunity Policy and the Rights of Persons with Disabilities Act, 2016, you have the right to non-discrimination in employment based on caste, religion, gender, or disability. The Shops and Establishments Act (State) protects young workers.' },
        { heading: 'Your Remedy', text: 'For workplace discrimination, file a complaint with the Equal Opportunity Commissioner or the Labour Commissioner. For intern exploitation, approach the National Human Rights Commission if there is a violation of fundamental rights.' },
        { heading: 'What To Do', text: 'Keep copies of your appointment letter and all workplace communications. If facing discrimination, file a written complaint with the HR department and keep copies. If no response within 30 days, approach the Labour Commissioner. For internships, ensure you have a written agreement specifying terms and conditions.' },
        { heading: 'Where To Go', citations: ['Equal Opportunity Policy', 'RPWD Act, 2016 — Section 21', 'State Shops and Establishments Act'] }
      ]
    },
    land: {
      title: 'Student Rights in Property Matters',
      sections: [
        { heading: 'Your Right', text: 'As a student, you have property rights under the Transfer of Property Act, 1882 and the Indian Succession Act, 1925. You have the right to inherit property and the right to be treated equally as an heir.' },
        { heading: 'Your Remedy', text: 'If your inheritance rights are denied, file a suit for partition in the civil court. For property disputes related to hostel or educational institution land, approach the relevant authority under the Education Act.' },
        { heading: 'What To Do', text: 'Obtain a copy of the Will or succession certificate. For inheritance disputes, consult a civil lawyer and file a suit under Section 9 of CPC. For institutional matters, approach the Registrar of the educational institution with supporting documents.' },
        { heading: 'Where To Go', citations: ['Transfer of Property Act, 1882', 'Indian Succession Act, 1925', 'CPC, 1908 — Section 9'] }
      ]
    },
    family: {
      title: 'Family Rights of Students',
      sections: [
        { heading: 'Your Right', text: 'Under the Right to Education Act, 2009, every child between 6-14 years has the right to free and compulsory education. The National Education Policy, 2020 ensures inclusive education. You also have the right to maintenance under the Hindu Minority and Guardianship Act, 1956.' },
        { heading: 'Your Remedy', text: 'For denial of admission, approach the District Education Officer. For maintenance disputes, file an application before the Maintenance Tribunal. For child rights violations, contact the National Commission for Protection of Child Rights (NCPCR).' },
        { heading: 'What To Do', text: 'For admission issues, file a complaint with the Block Education Officer with your Aadhaar and previous school certificates. For maintenance claims, gather evidence of expenses and file before the appropriate authority. For child rights issues, call the Childline (1098) or file a complaint online with the NCPCR.' },
        { heading: 'Where To Go', citations: ['RTE Act, 2009 — Section 4', 'National Education Policy, 2020', 'Childline: 1098'] }
      ]
    },
    housing: {
      title: 'Housing Rights of Students',
      sections: [
        { heading: 'Your Right', text: 'Under the University Grants Commission (UGC) guidelines, educational institutions must provide safe hostel facilities. The All India Council for Technical Education (AICTE) mandates adequate infrastructure for technical education students.' },
        { heading: 'Your Remedy', text: 'For hostel-related grievances, file a complaint with the institution\'s Grievance Redressal Committee as mandated by UGC regulations. If unresolved, approach the UGC or AICTE with supporting documents.' },
        { heading: 'What To Do', text: 'Document the issues with photographs and written records. File a formal complaint with the hostel warden and the institution\'s Grievance Redressal Cell. For persistent issues, file a complaint on the UGC online grievance portal (ugc.ac.in). For safety concerns, approach the local police.' },
        { heading: 'Where To Go', citations: ['UGC Regulations on Grievance Redressal', 'AICTE Norms', 'UGC Online Grievance Portal'] }
      ]
    },
    money: {
      title: 'Financial Rights of Students',
      sections: [
        { heading: 'Your Right', text: 'Under the Scholarships scheme of the Ministry of Social Justice and Empowerment, eligible students have the right to receive post-matric and pre-matric scholarships. The Reserve Bank of India permits education loans at concessional rates under the Credit Guarantee Fund Scheme.' },
        { heading: 'Your Remedy', text: 'For scholarship delays, file a complaint with the scholarship portal helpline or the district scholarship committee. For education loan issues, approach the Banking Ombudsman.' },
        { heading: 'What To Do', text: 'Apply for scholarships through the National Scholarship Portal (scholarships.gov.in) with required documents. For education loan issues, approach the bank\'s Nodal Officer first. If unresolved within 30 days, file a complaint with the Banking Ombudsman. For private education loan disputes, approach the consumer forum.' },
        { heading: 'Where To Go', citations: ['National Scholarship Portal', 'Credit Guarantee Fund Scheme', 'RBI Banking Ombudsman'] }
      ]
    },
    safety: {
      title: 'Safety Rights of Students',
      sections: [
        { heading: 'Your Right', text: 'Under the Protection of Children from Sexual Offences (POCSO) Act, 2012, students below 18 years have special protection against sexual offences. The Juvenile Justice (Care and Protection of Children) Act, 2015 provides for care and protection of vulnerable children.' },
        { heading: 'Your Remedy', text: 'For any form of abuse, call Childline (1098) immediately. For POCSO offences, the police are mandated to register an FIR without delay. For bullying or ragging, approach the Anti-Ragging Committee mandated by UGC regulations.' },
        { heading: 'What To Do', text: 'Report any incident to Childline (1098) and the local police. For ragging, file a complaint with the institution\'s Anti-Ragging Committee and the UGC Anti-Ragging helpline (1800-180-5522). Preserve all evidence and seek medical attention if needed. For POCSO offences, the statement will be recorded by a female officer in the presence of a parent or guardian.' },
        { heading: 'Where To Go', citations: ['POCSO Act, 2012 — Section 4', 'JJ Act, 2015', 'UGC Anti-Ragging Regulations', 'Childline: 1098'] }
      ]
    }
  },
  entrepreneur: {
    employment: {
      title: 'Employment Rights for Entrepreneurs',
      sections: [
        { heading: 'Your Right', text: 'Under the Shops and Establishments Act (State), you have the right to register your business and operate without arbitrary closure. The Micro, Small and Medium Enterprises Development Act, 2006 provides for delayed payment remedies.' },
        { heading: 'Your Remedy', text: 'For delayed payments by buyers, file an application with the Micro and Small Enterprises Facilitation Council under Section 18 of the MSMED Act, 2006. For arbitrary closure threats, approach the Labour Commissioner.' },
        { heading: 'What To Do', text: 'Register your MSME on the Udyam Portal (udyamregistration.gov.in). Maintain all contracts and invoices. For delayed payments exceeding 45 days, send a written demand and file with the MSEFC within the prescribed time. For regulatory compliance, consult the respective state authority.' },
        { heading: 'Where To Go', citations: ['MSMED Act, 2006 — Section 18', 'Udyam Registration Portal', 'State Shops and Establishments Act'] }
      ]
    },
    land: {
      title: 'Property Rights for Entrepreneurs',
      sections: [
        { heading: 'Your Right', text: 'Under the Companies Act, 2013, your business property is protected as corporate property. The Real Estate Regulation and Development Act, 2016 protects your investment in commercial real estate.' },
        { heading: 'Your Remedy', text: 'For commercial property disputes, file a suit under CPC. For RERA violations by commercial builders, file a complaint with the state RERA. For lease disputes, approach the Rent Control Court.' },
        { heading: 'What To Do', text: 'Maintain clear title documents and lease agreements for all business premises. For property disputes, engage a property lawyer to verify title and file appropriate suits. For RERA complaints, file online with the state RERA authority with all supporting documents.' },
        { heading: 'Where To Go', citations: ['Companies Act, 2013 — Section 185', 'RERA Act, 2016', 'CPC, 1908 — Section 9'] }
      ]
    },
    family: {
      title: 'Family & Business Succession Rights',
      sections: [
        { heading: 'Your Right', text: 'Under the Indian Partnership Act, 1932 and the Companies Act, 2013, you have the right to regulate business succession. The Hindu Succession Act, 1956 governs personal succession to business assets.' },
        { heading: 'Your Remedy', text: 'For partnership disputes, file a suit under the Indian Partnership Act. For company-related disputes, approach the National Company Law Tribunal (NCLT) under the Companies Act, 2013. For succession disputes, file a civil suit.' },
        { heading: 'What To Do', text: 'Draft a clear partnership deed or shareholders\' agreement specifying succession and exit terms. For NCLT matters, file under the appropriate section with supporting documents. For personal succession, consult a succession lawyer and apply for a succession certificate from the District Court.' },
        { heading: 'Where To Go', citations: ['Indian Partnership Act, 1932', 'Companies Act, 2013 — Section 241', 'Hindu Succession Act, 1956'] }
      ]
    },
    housing: {
      title: 'Commercial Housing Rights for Entrepreneurs',
      sections: [
        { heading: 'Your Right', text: 'Under the Real Estate (Regulation and Development) Act, 2016, commercial properties are covered under RERA. You have the right to possession on time and to compensation for delays.' },
        { heading: 'Your Remedy', text: 'For delayed possession of commercial property, file a complaint with the state RERA authority. You may also seek compensation under the Consumer Protection Act, 2019.' },
        { heading: 'What To Do', text: 'Register your commercial property purchase with the state RERA authority. Maintain all agreements and payment receipts. For delays beyond the agreed possession date, file a complaint under Section 18 of RERA for refund with interest or compensation.' },
        { heading: 'Where To Go', citations: ['RERA Act, 2016 — Section 18', 'Consumer Protection Act, 2019'] }
      ]
    },
    money: {
      title: 'Financial Rights for Entrepreneurs',
      sections: [
        { heading: 'Your Right', text: 'Under the Insolvency and Bankruptcy Code, 2016, you have the right to restructure or resolve insolvency. The MSME Act, 2006 protects against delayed payments. The Goods and Services Tax Act, 2017 provides for input tax credit and compliance framework.' },
        { heading: 'Your Remedy', text: 'For financial distress, initiate proceedings under the IBC through the National Company Law Tribunal. For delayed payments by corporates, file under Section 18 of the MSMED Act. For GST disputes, approach the GST Appellate Tribunal.' },
        { heading: 'What To Do', text: 'For IBC proceedings, file an application with the NCLT with evidence of default. For MSMED claims, file with the MSEFC with invoices and contracts. For GST disputes, first file an appeal with the GST Appellate Authority within 3 months of the order. Maintain all financial records and statutory filings.' },
        { heading: 'Where To Go', citations: ['IBC, 2016 — Section 7', 'MSMED Act, 2006 — Section 18', 'GST Act, 2017 — Section 107'] }
      ]
    },
    safety: {
      title: 'Business Safety Rights for Entrepreneurs',
      sections: [
        { heading: 'Your Right', text: 'Under the Intellectual Property Rights Act, 2005, your trademarks, patents, and copyrights are protected. The Information Technology Act, 2000 protects your digital assets and business data.' },
        { heading: 'Your Remedy', text: 'For IP infringement, file a suit in the appropriate High Court or the Intellectual Property Appellate Board. For cybercrime, file an FIR under the IT Act and approach the Cyber Crime Cell.' },
        { heading: 'What To Do', text: 'Register your trademarks with the Controller General of Patents, Designs and Trade Marks. For patent protection, file an application with the Indian Patent Office. For IP infringement, send a cease and desist notice and file for an injunction. For cybercrime, report to the Cyber Crime Cell and file online at cybercrime.gov.in.' },
        { heading: 'Where To Go', citations: ['IPR Act, 2005 — Section 104', 'IT Act, 2000 — Section 66', 'cybercrime.gov.in'] }
      ]
    }
  },
  other: {
    employment: {
      title: 'Employment Rights',
      sections: [
        { heading: 'Your Right', text: 'Under the Constitution of India, Article 19(1)(g), you have the right to practise any profession or carry on any occupation, trade or business. The Industrial Disputes Act, 1947 and the Code on Wages, 2019 protect your rights as an employee.' },
        { heading: 'Your Remedy', text: 'For workplace rights violations, file a complaint with the Labour Commissioner. For wage disputes, approach the appropriate authority under the Code on Wages. For industrial disputes, refer to the mechanism under the Industrial Disputes Act.' },
        { heading: 'What To Do', text: 'Maintain your employment contract, offer letter, and salary slips. For workplace grievances, use the internal grievance mechanism first. If unresolved, file a complaint with the Labour Commissioner or the appropriate tribunal.' },
        { heading: 'Where To Go', citations: ['Constitution of India — Article 19(1)(g)', 'Code on Wages, 2019', 'Industrial Disputes Act, 1947'] }
      ]
    },
    land: {
      title: 'Land and Property Rights',
      sections: [
        { heading: 'Your Right', text: 'Under the Transfer of Property Act, 1882 and the Indian Registration Act, 1908, you have the right to own, transfer, and register property. The Specific Relief Act, 1963 provides for specific performance of contracts.' },
        { heading: 'Your Remedy', text: 'For property disputes, file a suit for declaration and partition in the civil court. For registration disputes, approach the Sub-Registrar under the Indian Registration Act. For specific performance, file a suit under Section 14 of the Specific Relief Act.' },
        { heading: 'What To Do', text: 'Verify the property title through a title search at the Sub-Registrar office. Obtain an encumbrance certificate before purchase. For disputes, engage a property lawyer to file the appropriate suit under CPC. For urgent matters, apply for interim injunction under Order XXXIX of CPC.' },
        { heading: 'Where To Go', citations: ['Transfer of Property Act, 1882', 'Indian Registration Act, 1908 — Section 17', 'Specific Relief Act, 1963 — Section 14'] }
      ]
    },
    family: {
      title: 'Family and Personal Law Rights',
      sections: [
        { heading: 'Your Right', text: 'Under the Hindu Marriage Act, 1955, the Special Marriage Act, 1954, and other personal laws, you have rights related to marriage, divorce, custody, and maintenance. Section 125 CrPC provides for maintenance irrespective of religion.' },
        { heading: 'Your Remedy', text: 'For matrimonial disputes, file a petition in the appropriate Family Court. For maintenance claims, file under Section 125 CrPC or the relevant personal law. For custody disputes, approach the Family Court under the Guardians and Wards Act, 1890.' },
        { heading: 'What To Do', text: 'For divorce or separation, consult a family lawyer and file a petition under the appropriate personal law. For maintenance, file under Section 125 CrPC with proof of income and expenses. For child custody, file under the Guardians and Wards Act with evidence of the child\'s welfare.' },
        { heading: 'Where To Go', citations: ['Hindu Marriage Act, 1955', 'Special Marriage Act, 1954', 'CrPC, 1973 — Section 125', 'Guardians and Wards Act, 1890'] }
      ]
    },
    housing: {
      title: 'Housing Rights',
      sections: [
        { heading: 'Your Right', text: 'Under the Right to Fair Compensation and Transparency in Land Acquisition Act, 2013, you have protection against arbitrary land acquisition. The Real Estate (Regulation and Development) Act, 2016 protects homebuyers from builder defaults.' },
        { heading: 'Your Remedy', text: 'For builder default, file a complaint with the state RERA authority. For unfair eviction, approach the Rent Control Court. For government housing schemes, file a grievance with the housing authority.' },
        { heading: 'What To Do', text: 'For RERA complaints, file online with the state RERA authority. For rental disputes, file with the Rent Control Court or approach the civil court. For government housing, apply through the respective state housing board with required documents.' },
        { heading: 'Where To Go', citations: ['RERA Act, 2016', 'LARR Act, 2013', 'State Rent Control Act'] }
      ]
    },
    money: {
      title: 'Financial Rights',
      sections: [
        { heading: 'Your Right', text: 'Under the Reserve Bank of India Act, 1934 and the Banking Regulation Act, 1949, you have the right to fair banking services. The Consumer Protection Act, 2019 covers financial services. The RBI mandates fair practices in lending.' },
        { heading: 'Your Remedy', text: 'For banking grievances, approach the Banking Ombudsman. For insurance disputes, approach the Insurance Ombudsman. For securities issues, file with SEBI. For other financial complaints, approach the consumer forum.' },
        { heading: 'What To Do', text: 'First approach the bank\'s Grievance Redressal Officer with your complaint. If unresolved within 30 days, approach the Banking Ombudsman. Maintain all financial documents and correspondence. For investment fraud, report to SEBI and the local police.' },
        { heading: 'Where To Go', citations: ['RBI Banking Ombudsman Scheme', 'Insurance Ombudsman', 'SEBI Complaints Portal'] }
      ]
    },
    safety: {
      title: 'Safety and Protection Rights',
      sections: [
        { heading: 'Your Right', text: 'Under Article 21 of the Constitution, you have the fundamental right to life and personal liberty. The Indian Penal Code, 1860 and the Code of Criminal Procedure, 1973 provide comprehensive protection against criminal offences.' },
        { heading: 'Your Remedy', text: 'For any criminal offence, file an FIR at the nearest police station under Section 154 CrPC. The police are duty-bound to register the FIR. For human rights violations, approach the National Human Rights Commission or the State Human Rights Commission.' },
        { heading: 'What To Do', text: 'For emergencies, dial 100 for police or 112 for emergency services. For non-emergencies, file a written complaint at the police station and obtain a copy of the FIR. If the police refuse to register an FIR, approach the Superintendent of Police under Section 154(3) CrPC or file a complaint with the Magistrate under Section 156(3) CrPC.' },
        { heading: 'Where To Go', citations: ['Constitution of India — Article 21', 'IPC, 1860', 'CrPC, 1973 — Section 154', 'NHRC'] }
      ]
    }
  }
};
