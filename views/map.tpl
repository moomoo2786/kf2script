<div class="map" width="220">
    <div align="center">
        <a href="{{url}}">
        <img src="{{previewUrl}}" width="200" height="200">
        </a>
    </div>
    <div>
        {{name}}
    </div>
    <div>
        <img src="/static/{{rating}}">
    </div>
    <div>
        by&nbsp;{{author}}
    </div>

    <div>
        <form action="/{{'subscribe' if not checked else 'unsubscribe'}}/{{id}}">
        <button class="{{'subscribe' if not checked else 'unsubscribe'}}" type="submit">
            {{'subscribe' if not checked else 'unsubscribe'}}
        </button>
        </form>
    </div>
</div>