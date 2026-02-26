from src.format import MessageType, detect_message_type


def test_detect_message_type_quote() -> None:
    text = "🌟监控到新推文引用"
    assert detect_message_type(text) == MessageType.NEW_TWEET_QUOTE


def test_detect_message_type_reply() -> None:
    text = "🌟监控到新推文回复"
    assert detect_message_type(text) == MessageType.NEW_TWEET_REPLY


def test_detect_message_type_unknown() -> None:
    text = "this is a normal message"
    assert detect_message_type(text) == MessageType.UNKNOWN
