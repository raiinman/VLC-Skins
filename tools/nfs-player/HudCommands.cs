// Consume each native signal once, after observing this session's ready layout.
sealed class HudCommands
{
    bool armed;
    internal int Observe(int width,bool valid,bool available)
    {
        if(!valid) {armed=false;return 0;}
        if(width==211) {armed=true;return 0;}
        bool accept=armed && available && (width==212 || width==213);
        armed=false;
        return accept ? width-211 : 0;
    }
}

// Separate from YouTube playback: local media and an idle playlist can clear too.
sealed class PlaylistClearCommands
{
    bool armed;
    internal bool Observe(int width,bool valid,bool available)
    {
        if(!valid) {armed=false;return false;}
        if(width==161) {armed=true;return false;}
        bool accept=armed && available && width==162;
        armed=false;
        return accept;
    }
}
