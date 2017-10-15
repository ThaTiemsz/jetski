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
    this.state = {
      stats: null
    };

    globalState.getCurrentUser().then((user) => {
      this.setState({user});
    });

    globalState.getStats((stats) => {
      this.setState({stats});
    });
  //   this.getStuff();
  // }

  // async getStuff() {
  //   await globalState.getCurrentUser();
  //   await globalState.getStats();
  }

  render() {
    let statsPanels = [];
    console.log(this.state)

    if (globalState.user.admin) {
      statsPanels.push(
          <StatsPanel color='primary' icon='comments' data={this.state.stats.messages} text='Messages' key='messages' />
      );
      statsPanels.push(
          <StatsPanel color='green' icon='server' data={this.state.stats.guilds} text='Guilds' key='guilds' />
      );
      statsPanels.push(
          <StatsPanel color='yellow' icon='user' data={this.state.stats.users} text='Users' key='users' />
      );
      statsPanels.push(
          <StatsPanel color='red' icon='hashtag' data={this.state.stats.channels} text='Channels' key='channels' />
      );
    }

    return (
      <div className="row">
        {statsPanels}
      </div>
    );
  }
}

class Dashboard extends Component {
  render() {
		return (
      <div>
        <PageHeader name="Dashboard" />
        <Stats />
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
