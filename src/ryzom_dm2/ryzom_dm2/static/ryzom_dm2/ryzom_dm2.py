""" MUICSS Transcrypt to be compiled to Javascript for the browser.

    Use inner lambda workaround for correct transpilation of anonymous funcs.
    https://github.com/QQuick/Transcrypt/issues/36#issuecomment-213022299
"""
# Alias jQuery as 'S'. Use 'S__' to prefix jQuery object variables.
# __pragma__('alias', 'S', '$')

# Avoid static checking errors.
# __pragma__('skip')
jQuery = S = setTimeout = document = mui = this = 0
# __pragma__('noskip')


def muiSidedrawer(S):

    S__bodyEl = S('body')
    S__sidedrawerEl = S('#sidedrawer')

    def showSidedrawer():
        # show overlay
        options = {
            'onclose':
                (lambda:
                    S__sidedrawerEl
                    .removeClass('active')
                    .appendTo(document.body))
        }

        S__overlayEl = S(mui.overlay('on', options))

        # show element
        S__sidedrawerEl.appendTo(S__overlayEl)

        setTimeout(
            (lambda:
                S__sidedrawerEl.addClass('active')),
            20
        )

    def hideSidedrawer():
        S__bodyEl.toggleClass('hide-sidedrawer')

    S('.js-show-sidedrawer').on('click', showSidedrawer)
    S('.js-hide-sidedrawer').on('click', hideSidedrawer)

    S__titleEls = S('strong', S__sidedrawerEl)

    S__titleEls.js_next().hide()

    # Builtin alias 'js_next()' for 'next()'.
    S__titleEls.on(
        'click',
        (lambda:
            S(this).js_next().slideToggle(200))
    )


# jQuery(document).ready(function($){ muiSidedrawer($); });
# TODO: Handle jQuery.noConflict().
jQuery(lambda S: muiSidedrawer(S))
