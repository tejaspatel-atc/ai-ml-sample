from app.logger import logger
from app.settings import settings
from supabase import Client, create_client

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_API_KEY)


def fetch_bot_details(bot_id: str):
    """
    Fetch details of a bot from the Supabase database.

    This function retrieves information from the "bots" table in the Supabase
    database based on the provided `bot_id`. The details include the
    `gpt_assistant_id` and `gpt_vector_store_id` fields. If the bot is found,
    the corresponding data is returned. In case of an error during the
    database query, the error is logged, and an empty dictionary is returned.

    Parameters
    ----------
    bot_id : str
        The ID of the bot to fetch details for.

    Returns
    -------
    dict
        A dictionary containing the bot details if found, with keys
        `gpt_assistant_id` and `gpt_vector_store_id`. If no bot is found,
        an empty dictionary is returned.

    Raises
    ------
    Exception
        If an error occurs during the database query, it is logged, and raise the error.
    """
    try:
        response = (
            supabase.table("bots")
            .select(
                "gpt_assistant_id",
                "gpt_vector_store_id",
                "active",
                "greeting",
                "billing_status",
            )
            .eq("bot_id", bot_id)
            .maybe_single()
            .execute()
        )
        if response:
            return response.data
        else:
            return {}
    except Exception as e:
        logger.error(
            "Error occurred while fetching supabase details: %s; at line no: %s",
            (str(e), str(e.__traceback__.tb_lineno)),
        )
        raise e
