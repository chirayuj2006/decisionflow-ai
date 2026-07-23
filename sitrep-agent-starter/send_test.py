import requests

url = "http://localhost:9002/test"
payload = {
    "task": {"title": "DecisionFlow AI Report"},
    "summary": """
    Sarah: Okay, let's dive in. First item on the agenda is the infrastructure for the new microservices. We need to finalize our cloud provider before Sprint 3 starts.
    Alex: I've said this before, but I really think we should stick with AWS. We already know it, the AWS CDK is great, and migrating our existing services is a headache we just don't have time for right now. 
    David: I hear you, Alex, but GCP just approved us for $100k in startup credits. That literally covers our entire hosting budget for the next twelve months. Plus, GKE (Google Kubernetes Engine) is way easier for our current team size to manage. 
    Sarah: Okay, it sounds like the cost benefit heavily outweighs the learning curve. Are we officially deciding to switch all new development to GCP?
    Alex: Yeah, fine. I agree the money makes it necessary. I'll update the architecture docs this afternoon.
    Sarah: What's the realistic launch date, then? 
    Alex: We need to push the Beta launch back by two weeks. September 1st is the earliest we can guarantee stability.
    """,
    "attendees": [],
    "agent": {}
}

response = requests.post(url, json=payload)
print(response.json())