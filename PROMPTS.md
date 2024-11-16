# Prompts used

## Data collection

### Classifying domains given class name

```
Please analyze the provided descriptions and the details of the imported API, then determine the most fitting domain from a list of 31 labels.
Return like this domain - description, only the name of the selected domain and a brief description of this domain. 
API details: {classname}. Context: {possible_api_JSON}. Do not include any additional information or reasoning in your response.
```

### Classifying subdomains given class name and method name

```
Analyze the following information about the API function '{function_name}' which is part of the '{api_name}' in the '{api_domain}' domain.
Choose the most relevant classification from these available sub-domain options:

{sub_domains_json_filtered_by_api_domain}.


Please provide only the name of the most appropriate subdomain and the description of it, without any additional details or explanation.

```

## Training

### Training messages for binary classification domain model (per domain)

```
Classify a GitHub issue by indicating whether the domain [{domain}] is relevant to the issue given its title: [{issue_text}], 

body: [{issue_description}], and repository [{Repo_Name}]. Ensure that you Provide ONLY a list of relevant subdomains from the provided list. 

domain is relevant to the issue.
```

### Training messages for subdomain model (per domain)

```
Classify a GitHub issue by indicating whether each subdomain in the list [{subdomains}] is relevant to the issue given its title: [{issue_text}], 

and body: [{issue_description}]. Ensure that you provide ONLY a list of relevant subdomains and that each subdomain is in the list shown before
```

## Predictions

### Prediction message for domain

```
Classify a GitHub issue by indicating whether the following domain: [{domain}:{domain_description}] is relevant to the issue given its title: [{issue.title}],
body: [{issue.body}]. Ensure that you provide ONLY a 0 (not relevant) or a 1 (relevant) to determine whether the domains fits.
Example response: 0
```

### Prediction message for subdomain

```
Classify a GitHub issue by indicating TWO domains that are relevant to the issue based on its title: [{issue.title}] 
and body: [{issue.body}].

Prioritize positive precision by selecting a domain only when VERY CERTAIN it is relevant to the issue text.  Return as a JSON list with each key being the domain and value being a brief description of this domain. Refer to ONLY THESE domains when classifying: {subdomain_string}.


Important: Ensure that you provide the name of TWO domains in JSON LIST FORMAT. TWO DOMAINS: ie ["Application-Integration", "Cloud-Scalability"]

```
