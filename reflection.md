# Reflection on Assessment

## Key Design Decisions

My initial idea was to allow my agent to perform 3 different tasks 
- Produce a documentation containing API endpoints for developers to reference when creating frontend features
- Create onboarding forms that consists of questions that allows junior developers to answer to get exposed to the large and existing codebase
- Answer questions that users have regarding codebase 

So here's the **initial basic flow**
- Users are able to 
  - upload a Github Repo Link to the agent or
  - request a local folder to be scanned for the agent.
- From there, the agent is able to scan the codebase 

Since 

So I started on ```GithubAccessLink```class that consists of tools to scan through the github repo's codebase. But the Github Repo must be in public, and not private, as it requires going through the codebase on the Github website.
At the same time, I would also want to scan through local folders in the case the user simply just wants to look through local folders. 

From there, I got stuck on the functionality of scanning through Github.com's codebase and scanning through local folder at the same time. After discussion with Aaron, I could just clone the repo to a local folder and just scan through there. 

Now comes the ```CodebaseScanner``` class.
I approached it by retrieveing a deprecated example in the ConnectOnion's docs on creating documentation by scanning through the codebase for API endpoints and tried it on an example on UNSW DevSoc's Public repo (I believe it is from ```main3.py```). It is able to print out different API endpoints in the terminal. However, I felt that documentation like this is mostly included in the repos, and for those repos that doesn't have the documentation, it is ususally combined into a single code file which is easily referenced.

I also vibe coded an example of creating onboarding forms for junior developers to answer to get exposed to the codebase. For context, the format of a onboarding form looks something like this:
```
Which API route should you call if:

    you want a list of all applications for the current user?

    (your answer here)

    What HTTP method would you be making this API call with?

    (your answer here)

    What request body does this API call require (if it does not, explain why)?

    (your answer here)

    How would the response object for this API call look (if any)?

    (your answer here)
```

```
Explain what each line in this query is doing:

1. SELECT submitted, c.ends_at FROM applications a
2. JOIN campaigns c on c.id = a.campaign_id
3. WHERE a.id = 12345

    (your answer here)
    (your answer here)
    (your answer here)
```

Unfortunately, I accidentally deleted the vibe-coded code for it, but it was working last time.
But I think the problem is many companies have varying different ways of creating onboarding documents, which can be a bit different and hard to replicate. 


Overall, most of the problems is that it is too much work and code for ```agent.py``` can be too bloated with the amount of work the agent can do. Additionally, creating API documentation may not be an original idea to start off with. Hence, I decided to stick solely for agent to provide file recommendations and explanation of files for junior developers to ask. This is especially useful for junior developers to ask questions about a really big codebase. 

## Challenges

- Some of the debug features I still can't fix when implementing  ```xray.auto_debug()```, and still struggling with it
- Figuring out the actual flow including the menu items that user should consider 
- Refactoring code into smaller functions for usage in other functions 

## Improvements
- Most functions relies on other helper functions alot, so we can consider improving scalability if necessary 
- Some vibe coded code can be improved alot, since some functions feels very bloated, tried refactoring more but this breaks scalability and requires changes in many different functions
- More functions can be classified into different class (?)