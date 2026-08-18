"""
Text-to-SQL using Google Gemini
Converts natural language questions into SQL queries and executes them.
"""

import os
import re
from google import genai
from google.genai import types
from .sql_engine import execute_query, get_table_info

# Lazy client — only created when needed
_client = None


def get_client():
    """Get or create the Gemini client (lazy initialization)."""
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it with: export GEMINI_API_KEY=your_key_here"
            )
        _client = genai.Client(api_key=api_key)
    return _client


# System prompt for SQL generation
SYSTEM_PROMPT = """You are an NBA data analyst. Given a natural language question about NBA basketball, generate a SQL query to answer it.

You have access to these tables:

1. league_leaders - Player season averages
   Columns: player_id, player_name, team_abbreviation, points_per_game, rebounds_per_game, assists_per_game, steals_per_game, blocks_per_game, turnovers_per_game, field_goal_pct, three_point_pct, free_throw_pct, games_played, minutes_per_game

2. team_stats - Team season statistics
   Columns: team_id, team_name, wins, losses, points_per_game, rebounds_per_game, assists_per_game, field_goal_pct, three_point_pct

3. player_game_logs - Individual game logs
   Columns: player_id, player_name, team_abbreviation, game_date, matchup, win, points, rebounds, assists, steals, blocks, turnovers, minutes, field_goal_pct, three_point_pct, plus_minus

4. shot_chart - Shot location data
   Columns: grid_type, game_id, game_event_id, player_id, player_name, team_id, team_name, period, minutes_remaining, seconds_remaining, event_type, action_type, shot_type, shot_zone_basic, shot_zone_area, shot_zone_range, shot_distance, loc_x, loc_y, shot_attempted_flag, shot_made_flag, game_date, htm, vtm

Rules:
- Only generate SELECT queries (no INSERT, UPDATE, DELETE)
- Use standard SQL syntax compatible with SQLite
- Use ROUND() for decimal formatting
- Use ORDER BY and LIMIT for ranking questions
- Use GROUP BY for aggregation questions
- Return ONLY the SQL query, no explanations or markdown
"""


def generate_sql(question: str) -> str:
    """
    Generate a SQL query from a natural language question using Gemini.
    
    Args:
        question: Natural language question about NBA data
        
    Returns:
        SQL query string
    """
    client = get_client()
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )
    sql = response.text.strip()
    
    # Clean up the response - remove markdown code blocks if present
    sql = re.sub(r'```sql\s*', '', sql)
    sql = re.sub(r'```\s*', '', sql)
    sql = sql.strip()
    
    # Validate it's a SELECT query
    if not sql.upper().startswith("SELECT"):
        raise ValueError("Generated query is not a SELECT statement")
    
    return sql


def generate_natural_answer(question: str, sql: str, results: dict) -> str:
    """
    Generate a natural language answer from SQL results using Gemini.
    
    Args:
        question: Original question
        sql: The SQL query that was executed
        results: Query results with 'columns' and 'rows'
        
    Returns:
        Natural language response
    """
    client = get_client()
    
    # Format the results for the LLM
    columns = results.get("columns", [])
    rows = results.get("rows", [])
    
    if not rows:
        return "No results found for your question."
    
    # Create a readable table representation
    result_text = ", ".join(columns) + "\n"
    result_text += "---\n"
    for row in rows[:20]:  # Limit to 20 rows for context
        result_text += ", ".join(str(v) for v in row) + "\n"
    
    if len(rows) > 20:
        result_text += f"\n... and {len(rows) - 20} more rows"
    
    prompt = f"""Based on the following NBA data query results, provide a clear and concise answer to the user's question.

Question: {question}

SQL Query Used:
{sql}

Results:
{result_text}

Provide a natural language response that:
1. Directly answers the question
2. Highlights key insights or interesting patterns
3. Uses specific numbers from the data
4. Keeps it conversational and engaging (2-4 sentences)
"""
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text


def answer_question(question: str) -> dict:
    """
    Main function to answer a natural language question about NBA data.
    
    Args:
        question: Natural language question
        
    Returns:
        Dict with 'answer', 'sql', 'results', 'columns', 'rows'
    """
    # Generate SQL from question
    sql = generate_sql(question)
    
    # Execute the query
    results = execute_query(sql)
    
    if results.get("error"):
        return {
            "answer": f"I encountered an error while processing your question: {results['error']}",
            "sql": sql,
            "results": [],
            "columns": [],
            "rows": []
        }
    
    # Generate natural language answer
    answer = generate_natural_answer(question, sql, results)
    
    return {
        "answer": answer,
        "sql": sql,
        "results": results.get("rows", []),
        "columns": results.get("columns", []),
        "rows": results.get("rows", [])
    }
