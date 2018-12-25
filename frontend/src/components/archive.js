import React, { Component } from 'react';
import { globalState } from '../state';

export default class Archive extends Component {
  constructor() {
    super();

    this.state = {
      archive: null
    };
  }

  componentWillMount() {
    globalState.getArchive(this.props.params.aid).then((archive) => {
      this.setState({archive});
    });
  }

  render() {
    console.log("state", this.state.archive);
    console.log("id", this.props.params.aid);

    if (!this.state.archive) {
      return <h3>Loading...</h3>;
    }

    return (
      <div className="theme-dark messagesWrapper">
        <div className="divider-3gKybi divider-3zi9LO"><span className="dividerContent-2L12VI">#bot-spam (522859278546108416)</span></div>

        <div className="containerCompactBounded-cYR5cW containerCompact-3V0ioj container-1YxwTf">
          <div className="messageCompact-kQa7ES message-1PNnaP">
            <div className="contentCompact-1QLHBj content-3dzVd8 containerCompact-3pGPJs container-206Blv">
              <div className="buttonContainer-KtQ8wc">
                <div className="buttonContainer-37UsAw">
                  <div className="reactionBtn-2na4rd"></div>
                  <div className="button-3Jq0g9"></div>
                  <span className="messageId">(152164749868662784)</span>
                </div>
              </div>
              <div className="markup-2BOw-j isCompact-1hsne1"><h2 className="headerCompact-3wRt2W"><time className="latin12CompactTimeStamp-3v5WB3 timestampCompact-MHgFLv timestampCompactBase-26h38e" datetime="1499171000611"><i className="separatorLeft-3DZD2Q separator-1xUax1">[</i>2018-12-23 02:07:13 GMT+0<i className="separatorRight-3ctgKv separator-1xUax1">] </i></time><span className=""><span className="username-_4ZSMR">Tiemen<span className="discriminator">#0001</span></span><i className="separatorRight-3ctgKv separator-1xUax1">: </i></span></h2>haha yes! <a href="https://github.com/ThaTiemsz/jetski/blob/master/rowboat/plugins/admin.py" className="anchor-3Z-8Bb anchorUnderlineOnHover-2ESHQB" rel="noreferrer noopener" target="_blank">https://github.com/ThaTiemsz/jetski/blob/master/rowboat/plugins/admin.py</a> <span className="spoilerText-3p6IlD hidden-HHr2R9"><span className="inlineContent-3ZjPuv">is this server dead yet?</span></span></div>
            </div>
            <div className="containerCompact-3bB5aN container-1e22Ot"></div>
          </div>
          <hr aria-hidden="true" className="dividerEnabled-2TTlcf divider-32i8lo" />
        </div>

        <div className="containerCompactBounded-cYR5cW containerCompact-3V0ioj container-1YxwTf">
          <div className="messageCompact-kQa7ES message-1PNnaP">
            <div className="contentCompact-1QLHBj content-3dzVd8 containerCompact-3pGPJs container-206Blv">
              <div className="buttonContainer-KtQ8wc">
                <div className="buttonContainer-37UsAw">
                  <span className="messageId">(152164749868662784)</span>
                </div>
              </div>
              <div className="markup-2BOw-j isCompact-1hsne1"><h2 className="headerCompact-3wRt2W"><time className="latin12CompactTimeStamp-3v5WB3 timestampCompact-MHgFLv timestampCompactBase-26h38e" datetime="1499171000611"><i className="separatorLeft-3DZD2Q separator-1xUax1">[</i>2018-12-23 02:08:25 GMT+0<i className="separatorRight-3ctgKv separator-1xUax1">] </i></time><span className=""><span tabindex="0" className="username-_4ZSMR" role="button">Tiemen<span className="discriminator">#0001</span></span><i className="separatorRight-3ctgKv separator-1xUax1">: </i></span></h2>I'm sorry, but no. <code className="inline">SELECT name, MIN(date) FROM countdown WHERE status = 'enabled' GROUP BY category ORDER BY date ASC</code> <b>Haha YES!!!</b> <i>haha <b>nope</b></i> <u>yep</u> <s>nope</s></div>
            </div>
            <div className="containerCompact-3bB5aN container-1e22Ot">
              <a className="imageWrapper-2p5ogY imageZoom-1n-ADA clickable-3Ya1ho embedWrapper-3AbfJJ" href="https://cdn.discordapp.com/attachments/209719953706844161/395584117854568448/unknown.png" rel="noreferrer noopener" target="_blank" style="width: 400px; height: 268px;">
                <img alt="" src="https://media.discordapp.net/attachments/209719953706844161/395584117854568448/unknown.png?width=400&amp;height=269" style="width: 400px; height: 268px;" />
              </a>
            </div>
          </div>
          <hr aria-hidden="true" className="dividerEnabled-2TTlcf divider-32i8lo" />
        </div>
      </div>
    );
  }
}
