import React, { Component } from 'react';

import PageHeader from './page_header';
import GuildsTable from './guilds_table';
import {globalState} from '../state';


class DashboardGuildsList extends Component {
  constructor() {
    super();
    this.state = {guilds: null};
  }

  componentWillMount() {
    globalState.getCurrentUser().then((user) => {
      user.getGuilds().then((guilds) => {
        this.setState({guilds});
      });
    });
  }

  render() {
    return (
      <div className="panel panel-default">
        <div className="panel-heading">
          Guilds
        </div>
        <div className="panel-body">
          <GuildsTable guilds={this.state.guilds}/>
        </div>
      </div>
    );
  }
}

class StatsPanel extends Component {
  render () {
    const panelClass = `panel panel-${this.props.color}`;
    const iconClass = `fa fa-${this.props.icon} fa-5x`;

    return (
      <div className="col-lg-3 col-md-6">
        <div className={panelClass}>
          <div className="panel-heading">
            <div className="row">
              <div className="col-xs-3">
                <i className={iconClass}></i>
              </div>
              <div className="col-xs-9 text-right">
                <div className="huge">{this.props.data || 'N/A'}</div>
                <div>{this.props.text}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

class Stats extends Component {
  constructor() {
    super();
  //   this.getStuff();
  // }

  // async getStuff() {
  //   await globalState.getCurrentUser();
  //   await globalState.getStats();
  }

  componentWillMount() {
    globalState.getStats();
  }

  getStats() {
    let statsPanels = [];
    if (globalState.user.admin) {
      globalState.getStats((stats) => {
        statsPanels.push(
            <StatsPanel color='primary' icon='comments' data={stats.messages} text='Messages' key='messages' />
        );
        statsPanels.push(
            <StatsPanel color='green' icon='server' data={stats.guilds} text='Guilds' key='guilds' />
        );
        statsPanels.push(
            <StatsPanel color='yellow' icon='user' data={stats.users} text='Users' key='users' />
        );
        statsPanels.push(
            <StatsPanel color='red' icon='hashtag' data={stats.channels} text='Channels' key='channels' />
        );
      });
    }
    return statsPanels;
  }

  render() {
    const Panels = this.getStats();
    const oof = <StatsPanel color='primary' icon='comments' data='69' text='Messages' key='messages' />;
    console.log(panels)

    // return <div>{panels}</div>;
    return (
      <div>
        <Panels />
        {oof}
        {panels}
        <StatsPanel color='primary' icon='comments' data='N/A' text='Messages' key='messages' />
        <StatsPanel color='green' icon='server' data='N/A' text='Guilds' key='guilds' />
        <StatsPanel color='yellow' icon='user' data='N/A' text='Users' key='users' />
        <StatsPanel color='red' icon='hashtag' data='N/A' text='Channels' key='channels' />
      </div>
    )
  }
}

class Dashboard extends Component {
  render() {
		return (
      <div>
        <PageHeader name="Dashboard" />
        <div className="row">
          <Stats />
        </div>
        <div className="row">
          <div className="col-lg-12">
            <DashboardGuildsList />
          </div>
        </div>
      </div>
    );
  }
}

export default Dashboard;
