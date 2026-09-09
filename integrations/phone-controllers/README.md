# Phone controller integration

Contract and future adapter boundary for the existing DIY console. No server, phone app, pairing system, or Unity transport is implemented yet.

See [integration design](../../docs/phone-controllers.md). Game-side interfaces live in `game/Assets/_DarioKart/Scripts/Runtime/Input`. Keep standalone host/launcher adapters here only if the existing console needs them; don't duplicate its code without inspecting it.
