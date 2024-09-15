# Steps to follow:

1. Download reddit data from Academic torrents - either subreddit or entire reddit dump. 
   - Subreddit data will be in .zst format. One file for submissions and another for comments
   - Entire reddit dump, for each month ~50GB. Use `combine_folder_multiprocess.py` to extract subreddit data for each month, and then combine across months.
2. Use `filter_file.py` to extract subreddit data (submissions and comments) for specific time periods from the .zst files
3. `combine_submission_comments.py` to combine submissions and comments for each subreddit and write as a csv with following schema. 
   - Comments: Score, created_utc, author, permalink, link_id, body
   - Submissions: Score, created_utc, title, id, author, permalink, selftext
   - Submissions + Comments: id, title, selftext, body
4. `generation.py` and `prompt_generation_AI_work.txt` to generate text from the combined submissions and comments using LLMs. 1 LLM call for each post and all associated comments. Generates structured output within `output_raw` folder according to following schema:
```json{
  "anecdotes": [
    {
      "quote": "Full quote of a personal experience explicitly mentioning AI's impact on work",
      "summary": "Brief summary of the anecdote, with context if needed"
    }
  ],
  "media_reports": [
    {
      "quote": "Full quote discussing a media report about AI's impact on work",
      "summary": "Brief summary of the media report discussion, with context if needed"
    }
  ],
  "opinions": [
    {
      "quote": "Full quote expressing an opinion about AI's impact on work",
      "summary": "Brief summary of the opinion, with context if needed"
    }
  ],
  "other": [
    {
      "quote": "Full quote of other relevant content explicitly about AI's impact on work",
      "summary": "Brief summary of the other content, with context if needed"
    }
  ]
}
```

5. `extract_anecdotes.py` to extract only anecdotes from LLM output
6. `classification.py` and `prompt_classification_AI_work.txt` to generate labels for each of the anecdotes. The labels are:
   - Labor market risks (1)
   - Global AI divide (2)
   - Market concentration risks and single points of failure (3)
   - Risks to the environment (4)
   - Risks to privacy (5)
   - Copyright infringement (6)
   - Anecdotes unrelated to the impact of AI on work (7)
   
    The LLM output is structured as follows:
    ```
    {
         "categories": [1, 7, 1, 7]
    }
    ```
7. `combine_anecdotes_labels.py` to combine anecdotes and their respective labels in a CSV
8. `extract_anecdotes_category.py` to extract anecdotes with their respective categories in separate CSV

Statistics:
```
| Subreddit            | Cat 1 | Cat 2 | Cat 3 | Cat 4 | Cat 5 | Cat 6 | Cat 7 | Total |
|----------------------|-------|-------|-------|-------|-------|-------|-------|-------|
| ArtistLounge         |   500 |     2 |     1 |     0 |     1 |   104 |   686 |  1294 |
| Ask_Lawyers                  |    25 |     0 |     0 |     0 |     1 |     2 |    32 |    60 |
| creativewriting      |     1 |     0 |     0 |     0 |     0 |     0 |     0 |     1 |
| developersIndia      |  2272 |    15 |    16 |     0 |    15 |     4 |  3918 |  6240 |
| education            |    45 |     1 |     0 |     0 |     1 |     0 |   171 |   218 |
| freelanceWriters     |   875 |     5 |     2 |     0 |     3 |    21 |   295 |  1201 |
| Journalism           |   141 |     0 |     1 |     0 |     1 |     2 |   153 |   298 |
| medicine             |   193 |     1 |     7 |     0 |     0 |     1 |   965 |  1167 |
| musicians            |    49 |     0 |     0 |     0 |     0 |     4 |   150 |   203 |
| Music                |    77 |     0 |     1 |     0 |     0 |    12 |   172 |   262 |
| nursing              |   445 |     0 |     5 |     0 |    11 |     2 |  2568 |  3031 |
| paralegal            |   191 |     0 |     0 |     0 |     0 |     0 |   334 |   525 |
| Poetry               |     1 |     0 |     0 |     0 |     0 |     1 |     7 |     9 |
| Screenwriting        |   189 |     1 |     0 |     0 |     1 |     6 |   303 |   500 |
| softwaredevelopment  |    28 |     0 |     0 |     0 |     0 |     0 |    67 |    95 |
| SoftwareEngineering  |   163 |     0 |     0 |     0 |     0 |     0 |   182 |   345 |
| Teachers             |   866 |     3 |     0 |     0 |    13 |    23 |  2804 |  3709 |
| VoiceActing          |   210 |     1 |     0 |     0 |     1 |    11 |    78 |   301 |
| writers              |   184 |     2 |     0 |     0 |     2 |    15 |   326 |   529 |
| writing              |   192 |     0 |     1 |     0 |     2 |    16 |   485 |   696 |
|----------------------|-------|-------|-------|-------|-------|-------|-------|-------|
| Total                |  6647 |    31 |    34 |     0 |    52 |   224 | 13696 | 20684 |
```
## Relevant Threads and Links

- Top 40k subreddits: 2005 to 12-2023
    - https://www.reddit.com/r/pushshift/s/18wjxKJUB9
    - https://academictorrents.com/details/56aa49f9653ba545f48df2e33679f014d2829c10 
    - Torrent file: reddit-subreddit-2005-2023.torrent 

- Monthly dumps 2005-06 to 2024-06 https://academictorrents.com/details/20520c420c6c846f555523babc8c059e9daa8fc5
    - Torrent file: reddit-monthly-2005-2024.torrent 

- Monthly dump statistics, schema of posts and comments data
https://docs.google.com/spreadsheets/d/1umjeU3eIi1V0m3efY2Hq1mbm2eczU2ct-bVJyB0RigE/htmlview

- Data processing scripts debugging: https://www.reddit.com/r/pushshift/s/owMJQkjPM5

- qBittorrent v4.6.6 works
- PRAW documentation: https://praw.readthedocs.io/en/latest/code_overview/models/comment.html

Acknowledgement: Grateful to `u/Watchful1` for pushshift processing scripts (https://github.com/Watchful1/PushshiftDumps/blob/master/scripts) and subreddit data for Dec 2022 - Aug 2024.